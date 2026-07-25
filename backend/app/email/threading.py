from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket import TicketComment
from app.email.schemas import InboundEmail


def resolve_thread(db: Session, organization_id, email: InboundEmail) -> Ticket | None:
    """Given an inbound email, find the existing Ticket it belongs to, or
    return None if this should start a brand-new ticket.

    Threading strategy, in order:
    1. In-Reply-To matches a known email_message_id -> that comment's ticket.
    2. Any id in References matches a known email_message_id -> that ticket.
    3. Ticket.email_thread_id matches In-Reply-To or any References entry
       (covers replies to a message we never stored the exact comment for,
       e.g. a very long thread where an intermediate reply was lost).
    This intentionally never matches on subject line alone — subject
    matching is unreliable (two unrelated "Re: Invoice" threads) and would
    risk merging unrelated conversations into one ticket."""

    candidate_ids: list[str] = []
    if email.in_reply_to:
        candidate_ids.append(email.in_reply_to)
    candidate_ids.extend(email.references)

    if not candidate_ids:
        return None

    comment = db.execute(
        select(TicketComment)
        .join(Ticket, Ticket.id == TicketComment.ticket_id)
        .where(Ticket.organization_id == organization_id, TicketComment.email_message_id.in_(candidate_ids))
    ).scalars().first()
    if comment:
        return db.get(Ticket, comment.ticket_id)

    ticket = db.execute(
        select(Ticket).where(
            Ticket.organization_id == organization_id,
            Ticket.email_thread_id.in_(candidate_ids),
        )
    ).scalars().first()
    return ticket