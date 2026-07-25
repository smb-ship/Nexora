import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import Ticket, TicketComment, TicketStatus, TicketCategory
from app.models.user import User
from app.core.customer_auth import require_customer
from app.schemas.customer_portal import (
    CustomerTicketCreate, CustomerTicketListItem, CustomerTicketDetail,
    CustomerTicketListResponse, CustomerCommentCreate, CustomerCommentOut,
    CustomerDashboardStats,
)
from app.workflows.engine import run_workflows
from app.workflows.enums import WorkflowTriggerType

router = APIRouter(prefix="/portal", tags=["customer-portal"])

OPEN_STATUSES = [TicketStatus.OPEN, TicketStatus.PENDING, TicketStatus.ON_HOLD]
CLOSED_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED]


def _check_ownership(ticket: Ticket | None, current_user: User) -> Ticket:
    if not ticket or ticket.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/dashboard", response_model=CustomerDashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    base_filter = Ticket.customer_id == current_user.id

    total = db.execute(select(func.count()).select_from(Ticket).where(base_filter)).scalar_one()
    open_count = db.execute(
        select(func.count()).select_from(Ticket).where(base_filter, Ticket.status.in_(OPEN_STATUSES))
    ).scalar_one()
    resolved_count = db.execute(
        select(func.count()).select_from(Ticket).where(base_filter, Ticket.status == TicketStatus.RESOLVED)
    ).scalar_one()
    closed_count = db.execute(
        select(func.count()).select_from(Ticket).where(base_filter, Ticket.status == TicketStatus.CLOSED)
    ).scalar_one()

    recent = db.execute(
        select(Ticket).where(base_filter).order_by(Ticket.updated_at.desc()).limit(5)
    ).scalars().all()

    return CustomerDashboardStats(
        total_tickets=total,
        open_tickets=open_count,
        resolved_tickets=resolved_count,
        closed_tickets=closed_count,
        recent_tickets=recent,
    )


@router.post("/tickets", response_model=CustomerTicketDetail, status_code=201)
def create_ticket(
    payload: CustomerTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    ticket = Ticket(
        organization_id=current_user.organization_id,
        subject=payload.subject,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        requester_name=current_user.full_name or current_user.email,
        requester_email=current_user.email,
        created_by=current_user.id,
        customer_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    run_workflows(db, WorkflowTriggerType.TICKET_CREATED, ticket)

    return ticket


@router.get("/tickets", response_model=CustomerTicketListResponse)
def list_my_tickets(
    q: str | None = Query(None, description="Search subject/description"),
    status: TicketStatus | None = Query(None),
    category: TicketCategory | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    stmt = select(Ticket).where(Ticket.customer_id == current_user.id)
    count_stmt = select(func.count()).select_from(Ticket).where(Ticket.customer_id == current_user.id)

    if q:
        search = f"%{q}%"
        search_filter = or_(Ticket.subject.ilike(search), Ticket.description.ilike(search))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
    if status:
        stmt = stmt.where(Ticket.status == status)
        count_stmt = count_stmt.where(Ticket.status == status)
    if category:
        stmt = stmt.where(Ticket.category == category)
        count_stmt = count_stmt.where(Ticket.category == category)

    total = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(Ticket.updated_at.desc()).offset(skip).limit(limit)
    items = db.execute(stmt).scalars().all()

    return CustomerTicketListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/tickets/{ticket_id}", response_model=CustomerTicketDetail)
def get_my_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    return _check_ownership(db.get(Ticket, ticket_id), current_user)


@router.get("/tickets/{ticket_id}/comments", response_model=list[CustomerCommentOut])
def list_ticket_comments(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    ticket = _check_ownership(db.get(Ticket, ticket_id), current_user)

    comments = db.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket.id, TicketComment.is_internal_note.is_(False))
        .order_by(TicketComment.created_at.asc())
    ).scalars().all()

    return [
        CustomerCommentOut(
            id=c.id, body=c.body, created_at=c.created_at,
            author_id=c.author_id, is_own_message=(c.author_id == current_user.id),
        )
        for c in comments
    ]


@router.post("/tickets/{ticket_id}/comments", response_model=CustomerCommentOut, status_code=201)
def add_ticket_comment(
    ticket_id: uuid.UUID,
    payload: CustomerCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    ticket = _check_ownership(db.get(Ticket, ticket_id), current_user)

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=current_user.id,
        body=payload.body,
        is_internal_note=False,
    )
    db.add(comment)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)

    run_workflows(db, WorkflowTriggerType.TICKET_COMMENT_ADDED, ticket)

    return CustomerCommentOut(
        id=comment.id, body=comment.body, created_at=comment.created_at,
        author_id=comment.author_id, is_own_message=True,
    )