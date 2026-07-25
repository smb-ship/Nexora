import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import Ticket, TicketComment, TicketStatus, TicketPriority, TicketSource
from app.models.ticket_read_receipt import TicketReadReceipt
from app.models.email import EmailInbox
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketOut, TicketDetailOut,
    TicketCommentCreate, TicketCommentOut, InboxCounts,
)
from app.api.deps import get_current_user
from app.core.permissions import require_permission, Permission
from app.models.user import User
from app.core.events import emit_event, EventType
from app.email.providers.service import EmailService, EmailServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])

OPEN_STATUSES = [TicketStatus.OPEN, TicketStatus.PENDING, TicketStatus.ON_HOLD]
ARCHIVED_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED]


def _attach_unread_flags(tickets: list[Ticket], user_id: uuid.UUID, db: Session) -> list[Ticket]:
    if not tickets:
        return tickets
    ticket_ids = [t.id for t in tickets]
    receipts = db.execute(
        select(TicketReadReceipt).where(
            TicketReadReceipt.user_id == user_id,
            TicketReadReceipt.ticket_id.in_(ticket_ids),
        )
    ).scalars().all()
    receipt_map = {r.ticket_id: r.last_read_at for r in receipts}
    for ticket in tickets:
        last_read = receipt_map.get(ticket.id)
        ticket.unread = last_read is None or ticket.updated_at > last_read  # type: ignore[attr-defined]
    return tickets


def _attach_reply_flags(tickets: list[Ticket], db: Session) -> list[Ticket]:
    """Computed the same way `unread` is: attached as a plain instance
    attribute right before serialization, not a stored column.

    Semantics: `replied = True` means the most recent PUBLIC comment on
    the ticket was written by someone other than the ticket's customer
    (i.e. staff answered last — we're waiting on them). A ticket with no
    customer_id (created directly by staff, not via portal/email) is
    treated as replied=True by default, since there's no customer message
    to be "waiting" on.

    Known tradeoff (flagged, not hidden): this issues one query per batch
    rather than a single indexed lookup. Fine at current scale; revisit
    with a materialized "last_public_comment_author_id" column on Ticket
    if the inbox grows large. See SAVE PROGRESS technical debt section.
    """
    if not tickets:
        return tickets
    ticket_ids = [t.id for t in tickets]
    comments = db.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id.in_(ticket_ids), TicketComment.is_internal_note.is_(False))
        .order_by(TicketComment.created_at.asc())
    ).scalars().all()

    last_public_author: dict[uuid.UUID, uuid.UUID] = {}
    for c in comments:
        last_public_author[c.ticket_id] = c.author_id  # last write wins, ascending order

    for ticket in tickets:
        last_author = last_public_author.get(ticket.id)
        if ticket.customer_id is None:
            ticket.replied = True  # type: ignore[attr-defined]
        elif last_author is None:
            ticket.replied = True  # type: ignore[attr-defined]  # no public comments yet at all
        else:
            ticket.replied = last_author != ticket.customer_id  # type: ignore[attr-defined]
    return tickets


def _check_org(ticket: Ticket | None, current_user: User) -> Ticket:
    if not ticket or ticket.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/", response_model=TicketOut, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_CREATE)),
):
    ticket = Ticket(
        organization_id=current_user.organization_id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        created_by=current_user.id,
        assigned_to=payload.assigned_to,
        team_id=payload.team_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    ticket.unread = False
    ticket.replied = True  # staff-created, nothing to wait on yet

    emit_event(
        db, EventType.TICKET_CREATED, ticket.organization_id,
        ticket=ticket,
        data={
            "ticket_id": str(ticket.id),
            "subject": ticket.subject,
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "requester_email": ticket.requester_email,
        },
    )

    return ticket


@router.get("/inbox/counts", response_model=InboxCounts)
def get_inbox_counts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org_filter = Ticket.organization_id == current_user.organization_id

    mine = db.execute(
        select(func.count()).select_from(Ticket).where(
            org_filter, Ticket.assigned_to == current_user.id, Ticket.status.in_(OPEN_STATUSES),
        )
    ).scalar_one()

    unassigned = db.execute(
        select(func.count()).select_from(Ticket).where(
            org_filter, Ticket.assigned_to.is_(None), Ticket.status.in_(OPEN_STATUSES),
        )
    ).scalar_one()

    all_open = db.execute(
        select(func.count()).select_from(Ticket).where(org_filter, Ticket.status.in_(OPEN_STATUSES))
    ).scalar_one()

    receipts_subq = (
        select(TicketReadReceipt.ticket_id, TicketReadReceipt.last_read_at)
        .where(TicketReadReceipt.user_id == current_user.id)
        .subquery()
    )
    unread_stmt = (
        select(func.count())
        .select_from(Ticket)
        .outerjoin(receipts_subq, receipts_subq.c.ticket_id == Ticket.id)
        .where(
            org_filter,
            Ticket.status.in_(OPEN_STATUSES),
            (receipts_subq.c.last_read_at.is_(None)) | (Ticket.updated_at > receipts_subq.c.last_read_at),
        )
    )
    unread = db.execute(unread_stmt).scalar_one()

    return InboxCounts(mine=mine, unassigned=unassigned, all_open=all_open, unread=unread)


@router.get("/", response_model=list[TicketOut])
def list_tickets(
    view: str | None = Query(None, pattern="^(mine|unassigned|all)$"),
    status: TicketStatus | None = Query(None),
    priority: TicketPriority | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=200),
    unread: bool | None = Query(None),
    archived: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Ticket).where(Ticket.organization_id == current_user.organization_id)

    if view == "mine":
        stmt = stmt.where(Ticket.assigned_to == current_user.id)
    elif view == "unassigned":
        stmt = stmt.where(Ticket.assigned_to.is_(None))

    if status:
        stmt = stmt.where(Ticket.status == status)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if assigned_to:
        stmt = stmt.where(Ticket.assigned_to == assigned_to)
    if archived is True:
        stmt = stmt.where(Ticket.status.in_(ARCHIVED_STATUSES))
    elif archived is False:
        stmt = stmt.where(Ticket.status.notin_(ARCHIVED_STATUSES))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Ticket.subject.ilike(pattern),
                Ticket.requester_name.ilike(pattern),
                Ticket.requester_email.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Ticket.updated_at.desc()).offset(skip).limit(limit)
    tickets = db.execute(stmt).scalars().all()
    _attach_unread_flags(tickets, current_user.id, db)
    _attach_reply_flags(tickets, db)

    # `unread`/`replied` are computed post-query (not DB columns), so
    # filtering on them happens here rather than in the SQL WHERE clause.
    # Tradeoff: pagination (skip/limit) is applied BEFORE this filter, so
    # a page can return fewer results than `limit` even when more match.
    # Acceptable for current scale; flagged as technical debt below.
    if unread is True:
        tickets = [t for t in tickets if t.unread]
    elif unread is False:
        tickets = [t for t in tickets if not t.unread]

    return tickets


@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket(ticket_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _check_org(db.get(Ticket, ticket_id), current_user)
    _attach_unread_flags([ticket], current_user.id, db)
    _attach_reply_flags([ticket], db)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_UPDATE_STATUS)),
):
    ticket = _check_org(db.get(Ticket, ticket_id), current_user)

    old_status = ticket.status
    old_priority = ticket.priority
    old_assigned_to = ticket.assigned_to

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    if update_data.get("status") == TicketStatus.CLOSED and ticket.closed_at is None:
        ticket.closed_at = datetime.now(timezone.utc)
    elif update_data.get("status") not in (None, TicketStatus.CLOSED):
        ticket.closed_at = None

    db.commit()
    db.refresh(ticket)
    _attach_unread_flags([ticket], current_user.id, db)
    _attach_reply_flags([ticket], db)

    if "status" in update_data and ticket.status != old_status:
        emit_event(
            db, EventType.TICKET_STATUS_CHANGED, ticket.organization_id,
            ticket=ticket,
            data={"ticket_id": str(ticket.id), "old_status": old_status.value, "new_status": ticket.status.value},
        )
    if "priority" in update_data and ticket.priority != old_priority:
        emit_event(
            db, EventType.TICKET_PRIORITY_CHANGED, ticket.organization_id,
            ticket=ticket,
            data={"ticket_id": str(ticket.id), "old_priority": old_priority.value, "new_priority": ticket.priority.value},
        )
    if "assigned_to" in update_data and ticket.assigned_to != old_assigned_to:
        assign_event = EventType.TICKET_ASSIGNED if ticket.assigned_to else EventType.TICKET_UNASSIGNED
        emit_event(
            db, assign_event, ticket.organization_id,
            ticket=ticket,
            data={"ticket_id": str(ticket.id), "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None},
        )

    return ticket


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_DELETE)),
):
    ticket = _check_org(db.get(Ticket, ticket_id), current_user)
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/{ticket_id}/comments", response_model=TicketCommentOut, status_code=201)
async def add_comment(
    ticket_id: uuid.UUID,
    payload: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.permissions import ROLE_PERMISSIONS  # local import to avoid a circular import at module load

    ticket = _check_org(db.get(Ticket, ticket_id), current_user)

    required = Permission.TICKET_INTERNAL_NOTE if payload.is_internal_note else Permission.TICKET_COMMENT
    if required not in ROLE_PERMISSIONS.get(current_user.role, set()):
        raise HTTPException(status_code=403, detail="You don't have permission to perform this action")

    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        body=payload.body,
        is_internal_note=payload.is_internal_note,
    )
    db.add(comment)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)

    if not payload.is_internal_note:
        emit_event(
            db, EventType.TICKET_COMMENT_ADDED, ticket.organization_id,
            ticket=ticket,
            data={"ticket_id": str(ticket.id), "comment_id": str(comment.id), "author_id": str(current_user.id)},
        )

        if ticket.inbox_id:
            inbox = db.execute(
                select(EmailInbox).where(
                    EmailInbox.id == ticket.inbox_id,
                    EmailInbox.organization_id == current_user.organization_id,
                )
            ).scalar_one_or_none()

            if inbox and inbox.is_active:
                try:
                    await EmailService(db).send_reply(ticket, comment, inbox)
                except EmailServiceError as exc:
                    logger.error("Email reply blocked for comment %s on ticket %s: %s", comment.id, ticket.id, exc)
                except Exception:
                    logger.exception("Unexpected error sending email reply for comment %s on ticket %s", comment.id, ticket.id)

    return comment


@router.post("/{ticket_id}/read", status_code=204)
def mark_ticket_read(ticket_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = _check_org(db.get(Ticket, ticket_id), current_user)

    receipt = db.execute(
        select(TicketReadReceipt).where(
            TicketReadReceipt.ticket_id == ticket.id, TicketReadReceipt.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if receipt:
        receipt.last_read_at = now
    else:
        db.add(TicketReadReceipt(ticket_id=ticket.id, user_id=current_user.id, last_read_at=now))
    db.commit()