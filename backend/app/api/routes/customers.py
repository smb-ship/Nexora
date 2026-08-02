import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_, func, case
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketComment, TicketStatus
from app.models.chat import ChatConversation, ChatVisitor
from app.models.customer_note import CustomerNote
from app.models.workflow import WorkflowExecutionLog
from app.core.security import hash_password
from app.core.permissions import require_permission, Permission
from app.schemas.customer import (
    CustomerCreate, CustomerListItem, PaginatedCustomers, CustomerDetailOut, CustomerStatsOut,
    CustomerTicketOut, CustomerChatSummaryOut, CustomerNoteCreate, CustomerNoteUpdate, CustomerNoteOut,
    TimelineItemOut,
)

router = APIRouter(prefix="/customers", tags=["customers"])

OPEN_STATUSES = [TicketStatus.OPEN, TicketStatus.PENDING, TicketStatus.ON_HOLD]
CLOSED_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED]

SORT_FIELDS = {"name", "email", "created_at", "total_tickets", "open_tickets", "last_seen"}


def _get_customer(db: Session, customer_id: uuid.UUID, current_user: User) -> User:
    customer = db.get(User, customer_id)
    if not customer or customer.organization_id != current_user.organization_id or customer.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _customer_ticket_ids(db: Session, customer_id: uuid.UUID) -> list[uuid.UUID]:
    return list(db.execute(select(Ticket.id).where(Ticket.customer_id == customer_id)).scalars().all())


@router.post("/", response_model=CustomerListItem, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    customer = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        organization_id=current_user.organization_id,
        role=UserRole.CUSTOMER,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return CustomerListItem(
        id=customer.id, email=customer.email, full_name=customer.full_name, is_active=customer.is_active,
        created_at=customer.created_at, total_tickets=0, open_tickets=0, last_seen=None,
    )


@router.get("/", response_model=PaginatedCustomers)
def list_customers(
    q: str | None = Query(None, description="Search name/email"),
    status_filter: str | None = Query(None, alias="status", pattern="^(active|inactive)$"),
    has_open_tickets: bool | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    """Single grouped query computes total_tickets/open_tickets/last_seen
    for every customer at once via LEFT JOIN + aggregate functions — no
    per-customer follow-up queries (no N+1). Total count is derived by
    wrapping the same filtered/grouped statement as a subquery, so the
    count reflects the exact same filters (including has_open_tickets,
    which only makes sense post-aggregation via HAVING)."""
    if sort not in SORT_FIELDS:
        sort = "created_at"

    total_tickets_expr = func.count(Ticket.id)
    open_tickets_expr = func.count(case((Ticket.status.in_(OPEN_STATUSES), 1)))
    last_seen_expr = func.max(Ticket.updated_at)

    base = (
        select(
            User,
            total_tickets_expr.label("total_tickets"),
            open_tickets_expr.label("open_tickets"),
            last_seen_expr.label("last_seen"),
        )
        .outerjoin(Ticket, Ticket.customer_id == User.id)
        .where(User.organization_id == current_user.organization_id, User.role == UserRole.CUSTOMER)
        .group_by(User.id)
    )

    if q:
        pattern = f"%{q}%"
        base = base.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if status_filter == "active":
        base = base.where(User.is_active.is_(True))
    elif status_filter == "inactive":
        base = base.where(User.is_active.is_(False))
    if date_from:
        base = base.where(User.created_at >= date_from)
    if date_to:
        base = base.where(User.created_at <= date_to)
    if has_open_tickets is True:
        base = base.having(open_tickets_expr > 0)
    elif has_open_tickets is False:
        base = base.having(open_tickets_expr == 0)

    sort_map = {
        "name": User.full_name, "email": User.email, "created_at": User.created_at,
        "total_tickets": total_tickets_expr, "open_tickets": open_tickets_expr, "last_seen": last_seen_expr,
    }
    sort_col = sort_map[sort]
    base = base.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()

    rows = db.execute(base.offset(skip).limit(limit)).all()
    items = [
        CustomerListItem(
            id=row.User.id, email=row.User.email, full_name=row.User.full_name,
            is_active=row.User.is_active, created_at=row.User.created_at,
            total_tickets=row.total_tickets, open_tickets=row.open_tickets, last_seen=row.last_seen,
        )
        for row in rows
    ]
    return PaginatedCustomers(items=items, total=total, skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    customer = _get_customer(db, customer_id, current_user)

    lifetime_tickets = db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.customer_id == customer_id)
    ).scalar_one()

    open_issues = db.execute(
        select(func.count()).select_from(Ticket).where(
            Ticket.customer_id == customer_id, Ticket.status.in_(OPEN_STATUSES),
        )
    ).scalar_one()

    closed_count = db.execute(
        select(func.count()).select_from(Ticket).where(
            Ticket.customer_id == customer_id, Ticket.status.in_(CLOSED_STATUSES),
        )
    ).scalar_one()
    resolution_rate = (closed_count / lifetime_tickets) if lifetime_tickets > 0 else None

    # Avg response time: for each of this customer's tickets, find the
    # first PUBLIC comment authored by someone other than the customer
    # (i.e. staff's first reply), then average (comment.created_at -
    # ticket.created_at) across tickets that have one. Computed in Python
    # over a single fetched dataset rather than N separate queries.
    ticket_rows = db.execute(
        select(Ticket.id, Ticket.created_at).where(Ticket.customer_id == customer_id)
    ).all()
    response_seconds: list[float] = []
    if ticket_rows:
        ticket_ids = [t.id for t in ticket_rows]
        ticket_created_map = {t.id: t.created_at for t in ticket_rows}
        first_staff_comments = db.execute(
            select(TicketComment.ticket_id, func.min(TicketComment.created_at))
            .where(
                TicketComment.ticket_id.in_(ticket_ids),
                TicketComment.is_internal_note.is_(False),
                TicketComment.author_id != customer_id,
            )
            .group_by(TicketComment.ticket_id)
        ).all()
        for ticket_id, first_reply_at in first_staff_comments:
            created_at = ticket_created_map.get(ticket_id)
            if created_at:
                response_seconds.append((first_reply_at - created_at).total_seconds())

    avg_response = sum(response_seconds) / len(response_seconds) if response_seconds else None

    return CustomerDetailOut(
        id=customer.id, email=customer.email, full_name=customer.full_name,
        is_active=customer.is_active, created_at=customer.created_at,
        stats=CustomerStatsOut(
            lifetime_tickets=lifetime_tickets, open_issues=open_issues,
            resolution_rate=resolution_rate, avg_response_seconds=avg_response,
        ),
    )


@router.get("/{customer_id}/tickets", response_model=list[CustomerTicketOut])
def get_customer_tickets(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    _get_customer(db, customer_id, current_user)
    return db.execute(
        select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc())
    ).scalars().all()


@router.get("/{customer_id}/chats", response_model=list[CustomerChatSummaryOut])
def get_customer_chats(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    """Soft match: ChatVisitor has no FK to User (visitors are anonymous
    by design — see Milestone 10). This matches by email within the same
    org. A customer who never gave an email during chat, or used a
    different email than their account, will not show up here — a real
    limitation, not a bug, given the current visitor model."""
    customer = _get_customer(db, customer_id, current_user)
    if not customer.email:
        return []

    visitor_ids = db.execute(
        select(ChatVisitor.id).where(
            ChatVisitor.organization_id == current_user.organization_id,
            ChatVisitor.email == customer.email,
        )
    ).scalars().all()
    if not visitor_ids:
        return []

    conversations = db.execute(
        select(ChatConversation).where(ChatConversation.visitor_id.in_(visitor_ids))
        .order_by(ChatConversation.created_at.desc())
    ).scalars().all()

    # message_count via a single grouped query rather than len(conv.messages)
    # per row (which would lazy-load N times).
    from app.models.chat import ChatMessage
    conv_ids = [c.id for c in conversations]
    count_rows = db.execute(
        select(ChatMessage.conversation_id, func.count(ChatMessage.id))
        .where(ChatMessage.conversation_id.in_(conv_ids))
        .group_by(ChatMessage.conversation_id)
    ).all() if conv_ids else []
    counts = dict(count_rows)

    return [
        CustomerChatSummaryOut(
            id=c.id, status=c.status.value, created_at=c.created_at,
            message_count=counts.get(c.id, 0),
        )
        for c in conversations
    ]


@router.get("/{customer_id}/timeline", response_model=list[TimelineItemOut])
def get_customer_timeline(
    customer_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    customer = _get_customer(db, customer_id, current_user)
    items: list[TimelineItemOut] = []

    tickets = db.execute(
        select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc()).limit(limit)
    ).scalars().all()
    for t in tickets:
        items.append(TimelineItemOut(
            type="ticket_created", timestamp=t.created_at,
            data={"ticket_id": str(t.id), "subject": t.subject, "status": t.status.value},
        ))

    if customer.email:
        visitor_ids = db.execute(
            select(ChatVisitor.id).where(
                ChatVisitor.organization_id == current_user.organization_id,
                ChatVisitor.email == customer.email,
            )
        ).scalars().all()
        if visitor_ids:
            conversations = db.execute(
                select(ChatConversation).where(ChatConversation.visitor_id.in_(visitor_ids))
                .order_by(ChatConversation.created_at.desc()).limit(limit)
            ).scalars().all()
            for c in conversations:
                items.append(TimelineItemOut(
                    type="chat_started", timestamp=c.created_at,
                    data={"conversation_id": str(c.id), "status": c.status.value},
                ))

    notes = db.execute(
        select(CustomerNote).where(CustomerNote.customer_id == customer_id)
        .order_by(CustomerNote.created_at.desc()).limit(limit)
    ).scalars().all()
    for n in notes:
        items.append(TimelineItemOut(
            type="note_added", timestamp=n.created_at,
            data={"note_id": str(n.id), "excerpt": n.body[:120]},
        ))

    ticket_ids = _customer_ticket_ids(db, customer_id)
    if ticket_ids:
        exec_logs = db.execute(
            select(WorkflowExecutionLog).where(WorkflowExecutionLog.ticket_id.in_(ticket_ids))
            .order_by(WorkflowExecutionLog.created_at.desc()).limit(limit)
        ).scalars().all()
        for log in exec_logs:
            items.append(TimelineItemOut(
                type="automation_triggered", timestamp=log.created_at,
                data={"ticket_id": str(log.ticket_id), "trigger_type": log.trigger_type.value, "success": log.success},
            ))

    items.sort(key=lambda i: i.timestamp, reverse=True)
    return items[:limit]


# --- Notes ---

@router.get("/{customer_id}/notes", response_model=list[CustomerNoteOut])
def list_customer_notes(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    _get_customer(db, customer_id, current_user)
    notes = db.execute(
        select(CustomerNote).where(CustomerNote.customer_id == customer_id).order_by(CustomerNote.created_at.desc())
    ).scalars().all()
    return [
        CustomerNoteOut(
            id=n.id, body=n.body, author_id=n.author_id,
            author_name=n.author.full_name if n.author else None,
            created_at=n.created_at, updated_at=n.updated_at,
        )
        for n in notes
    ]


@router.post("/{customer_id}/notes", response_model=CustomerNoteOut, status_code=201)
def create_customer_note(
    customer_id: uuid.UUID,
    payload: CustomerNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    _get_customer(db, customer_id, current_user)
    note = CustomerNote(
        organization_id=current_user.organization_id, customer_id=customer_id,
        author_id=current_user.id, body=payload.body,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return CustomerNoteOut(
        id=note.id, body=note.body, author_id=note.author_id,
        author_name=current_user.full_name, created_at=note.created_at, updated_at=note.updated_at,
    )


@router.patch("/{customer_id}/notes/{note_id}", response_model=CustomerNoteOut)
def update_customer_note(
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    payload: CustomerNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    note = db.get(CustomerNote, note_id)
    if not note or note.customer_id != customer_id or note.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Note not found")
    note.body = payload.body
    db.commit()
    db.refresh(note)
    return CustomerNoteOut(
        id=note.id, body=note.body, author_id=note.author_id,
        author_name=note.author.full_name if note.author else None,
        created_at=note.created_at, updated_at=note.updated_at,
    )


@router.delete("/{customer_id}/notes/{note_id}", status_code=204)
def delete_customer_note(
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    note = db.get(CustomerNote, note_id)
    if not note or note.customer_id != customer_id or note.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()