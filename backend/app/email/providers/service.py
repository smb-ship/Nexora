import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketComment, TicketSource, TicketStatus
from app.models.email import EmailInbox, EmailAttachment, EmailStatus
from app.models.user import User, UserRole
from app.email.schemas import InboundEmail, OutboundEmail, SendResult
from app.email.threading import resolve_thread
from app.email.providers.factory import get_email_provider, EmailProviderError
from app.ai.service import AIService, AIServiceError
from app.core.config import settings
from app.core.events import emit_event, EventType

logger = logging.getLogger(__name__)

# --- Retry configuration (Milestone 8, Phase F) ---
# Hand-rolled rather than a new dependency (e.g. tenacity) — simple enough
# to not warrant expanding requirements.txt. Move to app.core.config if
# this ever needs to be tunable per-environment.
MAX_SEND_ATTEMPTS = 3
RETRY_BACKOFF_BASE_SECONDS = 2  # attempt 1->2 waits 2s, 2->3 waits 4s


class EmailServiceError(Exception):
    pass


def _get_or_create_customer(db: Session, organization_id: uuid.UUID, email_address: str, display_name: str | None) -> User:
    """Finds an existing customer by email within this org, or creates one.
    Reuses the exact same construction pattern as the staff-facing
    POST /api/v1/customers/ endpoint (Milestone 7) — no separate customer
    creation logic for the email path."""
    from app.core.security import hash_password
    import secrets

    customer = db.query(User).filter(
        User.organization_id == organization_id,
        User.email == email_address,
        User.role == UserRole.CUSTOMER,
    ).first()
    if customer:
        return customer

    customer = User(
        email=email_address,
        full_name=display_name,
        hashed_password=hash_password(secrets.token_urlsafe(24)),  # unusable random password; email-only contact for now
        organization_id=organization_id,
        role=UserRole.CUSTOMER,
    )
    db.add(customer)
    db.flush()
    return customer


async def _send_with_retries(provider, outbound: OutboundEmail, ticket_id: uuid.UUID, comment_id: uuid.UUID) -> SendResult:
    """Retries a provider.send() call with exponential backoff. Treats
    both an explicit SendResult(success=False) AND an unexpected raised
    exception as retryable — base.py's contract says providers shouldn't
    raise for ordinary failures, but this doesn't trust that blindly
    across third-party provider implementations added later (defense in
    depth, not a violation of the interface contract)."""
    last_result: SendResult | None = None

    for attempt in range(1, MAX_SEND_ATTEMPTS + 1):
        try:
            result = await provider.send(outbound)
        except Exception as exc:
            logger.warning(
                "Email provider raised unexpectedly on attempt %s/%s (ticket=%s comment=%s): %s",
                attempt, MAX_SEND_ATTEMPTS, ticket_id, comment_id, exc,
            )
            result = SendResult(success=False, error=str(exc))

        if result.success:
            if attempt > 1:
                logger.info(
                    "Email send succeeded on retry attempt %s/%s (ticket=%s comment=%s)",
                    attempt, MAX_SEND_ATTEMPTS, ticket_id, comment_id,
                )
            return result

        last_result = result
        if attempt < MAX_SEND_ATTEMPTS:
            wait = RETRY_BACKOFF_BASE_SECONDS ** attempt
            logger.warning(
                "Email send failed on attempt %s/%s (ticket=%s comment=%s): %s — retrying in %ss",
                attempt, MAX_SEND_ATTEMPTS, ticket_id, comment_id, result.error, wait,
            )
            await asyncio.sleep(wait)

    logger.error(
        "Email send exhausted %s attempts (ticket=%s comment=%s): %s",
        MAX_SEND_ATTEMPTS, ticket_id, comment_id,
        last_result.error if last_result else "unknown error",
    )
    return last_result or SendResult(success=False, error="Unknown send failure")


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    async def process_inbound(self, inbox: EmailInbox, email: InboundEmail) -> TicketComment:
        """Entry point for every inbound email, regardless of which
        provider produced it. Threads to an existing ticket or creates a
        new one, reusing Ticket/TicketComment exactly as every other
        ticket-creation path does — then fires AI + workflows identically
        to Milestones 5 and 6, with zero duplicated business logic.

        Duplicate protection (Milestone 8, Phase F): the initial check
        below handles the common case (re-delivered webhook, retried
        request). The try/except around commit() is the concurrency-safe
        backstop — if two requests for the same Message-ID both pass the
        initial check before either commits, the DB's unique constraint on
        email_message_id rejects the second insert, and we catch that
        specifically instead of letting it 500."""

        existing = self.db.query(TicketComment).filter(TicketComment.email_message_id == email.message_id).first()
        if existing:
            logger.info("Duplicate inbound email Message-ID %s ignored (already stored)", email.message_id)
            return existing

        ticket = resolve_thread(self.db, inbox.organization_id, email)
        is_new_ticket = ticket is None

        customer = _get_or_create_customer(self.db, inbox.organization_id, email.from_address, None)

        if is_new_ticket:
            ticket = Ticket(
                organization_id=inbox.organization_id,
                subject=email.subject or "(no subject)",
                description=email.text_body,
                requester_name=customer.full_name or email.from_address,
                requester_email=email.from_address,
                created_by=customer.id,
                customer_id=customer.id,
                source=TicketSource.EMAIL,
                inbox_id=inbox.id,
                email_thread_id=email.message_id,
            )
            self.db.add(ticket)
            self.db.flush()

        comment = TicketComment(
            ticket_id=ticket.id,
            author_id=customer.id,
            body=email.text_body,
            is_internal_note=False,
            is_email=True,
            html_body=email.html_body,
            email_message_id=email.message_id,
            email_in_reply_to=email.in_reply_to,
            email_references=email.references,
            email_from=email.from_address,
            email_to=email.to_addresses,
            email_cc=email.cc_addresses,
            email_bcc=email.bcc_addresses,
            email_status=EmailStatus.RECEIVED.value,
        )
        self.db.add(comment)

        if not is_new_ticket:
            ticket.status = TicketStatus.OPEN if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED) else ticket.status
            ticket.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            logger.warning(
                "Race-condition duplicate inbound email Message-ID %s detected on commit; "
                "returning the already-committed comment instead of erroring",
                email.message_id,
            )
            winner = self.db.query(TicketComment).filter(TicketComment.email_message_id == email.message_id).first()
            if winner:
                return winner
            raise  # a genuinely different integrity error — don't swallow it

        self.db.refresh(ticket)
        self.db.refresh(comment)

        for att in email.attachments:
            self.db.add(EmailAttachment(
                comment_id=comment.id, filename=att.filename,
                content_type=att.content_type, size_bytes=att.size_bytes, storage_key=att.storage_key,
            ))
        if email.attachments:
            self.db.commit()

        # Reuse Milestone 5's AI service exactly as the agent-triggered AI
        # panel does — same prompts, same model, no duplication. Failures
        # here must never block the email pipeline itself.

        if is_new_ticket:
            try:
                ai = AIService()
                summary = await ai.summarize(ticket)
                sentiment, score = await ai.analyze_sentiment(ticket)
                priority = await ai.predict_priority(ticket)
                tags = await ai.suggest_tags(ticket)

                from app.models.ticket_ai_insight import TicketAIInsight
                insight = TicketAIInsight(
                    ticket_id=ticket.id, summary=summary, sentiment=sentiment, sentiment_score=score,
                    predicted_priority=priority, suggested_tags=tags,
                    model_used=settings.GEMINI_MODEL, generated_at=datetime.now(timezone.utc),
                )
                self.db.add(insight)
                self.db.commit()

                emit_event(
                    self.db, EventType.AI_COMPLETED, ticket.organization_id,
                    ticket=ticket,
                    data={
                        "ticket_id": str(ticket.id), "sentiment": sentiment,
                        "sentiment_score": score, "predicted_priority": priority, "suggested_tags": tags,
                    },
                )
            except AIServiceError as exc:
                logger.warning("AI insight generation failed for email-created ticket %s: %s", ticket.id, exc)

        # Reuse Milestone 6's workflow engine exactly as the agent/portal
        # paths do — identical triggers, so a rule like "email ticket
        # created -> assign to Support team" just works with no new code.
        # This now goes through the bus (Milestone 10) rather than calling
        # run_workflows directly; the workflow-engine subscriber (see
        # app/core/event_subscribers.py) still calls it exactly the same.
        ticket_event = EventType.TICKET_CREATED if is_new_ticket else EventType.TICKET_COMMENT_ADDED
        emit_event(
            self.db, ticket_event, ticket.organization_id,
            ticket=ticket,
            data={"ticket_id": str(ticket.id), "comment_id": str(comment.id), "is_new_ticket": is_new_ticket},
        )

        # Bus-only event — no workflow trigger mirrors this one. Webhook/n8n
        # subscribers (Phase B/C) use this to notify external systems that
        # an email arrived, independent of whether it created a new ticket
        # or just added a comment to an existing one.
        emit_event(
            self.db, EventType.EMAIL_RECEIVED, ticket.organization_id,
            ticket=ticket,
            data={
                "ticket_id": str(ticket.id), "comment_id": str(comment.id),
                "from_address": email.from_address, "subject": email.subject, "is_new_ticket": is_new_ticket,
            },
        )

        return comment

    async def send_reply(self, ticket: Ticket, comment: TicketComment, inbox: EmailInbox) -> SendResult:
        """Sends a public TicketComment as an outbound email reply,
        preserving thread headers. Called from tickets.py's add_comment
        hook (Phase D) — never called for internal notes, and the caller
        is responsible for that check (defense-in-depth: this method also
        refuses if asked to send one, see below).

        Provider-unavailable handling (Milestone 8, Phase F): if no
        provider implementation exists for this inbox's provider_type,
        that's caught here — at the source — rather than left for the
        caller to guess at, and reported the same way any other send
        failure is (SendResult, not a raised exception reaching tickets.py)."""
        if comment.is_internal_note:
            raise EmailServiceError("Internal notes must never be emailed.")

        try:
            provider = get_email_provider(inbox)
        except EmailProviderError as exc:
            logger.error(
                "Email provider unavailable for inbox %s (ticket=%s comment=%s): %s",
                inbox.id, ticket.id, comment.id, exc,
            )
            comment.is_email = True
            comment.email_status = EmailStatus.FAILED.value
            self.db.commit()
            return SendResult(success=False, error=str(exc))

        message_id = f"<{uuid.uuid4()}@{inbox.email_address.split('@')[-1]}>"
        references = list(dict.fromkeys([*_thread_references(self.db, ticket.id), ticket.email_thread_id or ""]))
        references = [r for r in references if r]

        outbound = OutboundEmail(
            message_id=message_id,
            from_address=inbox.email_address,
            to_addresses=[ticket.requester_email],
            subject=f"Re: {ticket.subject}",
            text_body=comment.body,
            html_body=comment.html_body,
            in_reply_to=ticket.email_thread_id,
            references=references,
        )

        result = await _send_with_retries(provider, outbound, ticket.id, comment.id)

        comment.is_email = True
        comment.email_message_id = message_id
        comment.email_in_reply_to = outbound.in_reply_to
        comment.email_references = references
        comment.email_from = inbox.email_address
        comment.email_to = outbound.to_addresses
        comment.email_status = EmailStatus.SENT.value if result.success else EmailStatus.FAILED.value
        self.db.commit()

        if not result.success:
            logger.error("Failed to send email reply for ticket %s after retries: %s", ticket.id, result.error)

        emit_event(
            self.db, EventType.EMAIL_SENT, ticket.organization_id,
            ticket=ticket,
            data={
                "ticket_id": str(ticket.id), "comment_id": str(comment.id),
                "to_addresses": outbound.to_addresses, "success": result.success,
                "error": result.error if not result.success else None,
            },
        )

        return result


def _thread_references(db: Session, ticket_id: uuid.UUID) -> list[str]:
    rows = db.query(TicketComment.email_message_id).filter(
        TicketComment.ticket_id == ticket_id, TicketComment.email_message_id.isnot(None)
    ).all()
    return [r[0] for r in rows]