import logging
import uuid
from datetime import datetime, timezone

from app.email.providers.base import EmailProvider
from app.email.schemas import OutboundEmail, SendResult

logger = logging.getLogger(__name__)


class DevelopmentEmailProvider(EmailProvider):
    """Simulates a real email provider without sending anything over the
    network. Outbound emails are captured in-memory (and logged) instead of
    delivered; inbound emails are simulated via the /api/v1/email-dev
    endpoints in Phase C, which call straight into EmailService exactly as
    a real provider's webhook handler would.

    Swapping this for a real provider later is purely a config change: set
    EmailInbox.provider_type to smtp/gmail/etc. and implement that
    provider's send() — nothing in EmailService, the ticket pipeline, or
    the frontend needs to change."""

    # Class-level so all instances (which are cheap, request-scoped) share
    # the same simulated outbox for the lifetime of the running process —
    # good enough for local dev/testing; not intended to survive a restart.
    _sent_log: list[dict] = []

    # --- Test hook (Milestone 8, Phase F) ---
    # Lets Phase G's end-to-end test exercise retry/failure handling
    # without a real provider outage. Does not affect production
    # providers at all — this class is dev-only by definition.
    _force_failures_remaining: int = 0

    @classmethod
    def simulate_failures(cls, count: int) -> None:
        """Make the next `count` send() calls fail before reverting to
        normal simulated success. Call this from a test/dev shell before
        triggering a reply to exercise EmailService's retry logic."""
        cls._force_failures_remaining = count

    async def send(self, email: OutboundEmail) -> SendResult:
        if DevelopmentEmailProvider._force_failures_remaining > 0:
            DevelopmentEmailProvider._force_failures_remaining -= 1
            remaining = DevelopmentEmailProvider._force_failures_remaining
            logger.warning(
                "DevelopmentEmailProvider: simulating send failure (test hook), %d more scheduled",
                remaining,
            )
            return SendResult(success=False, error="Simulated provider failure (test hook)")

        provider_message_id = f"<dev-{uuid.uuid4()}@nexora.dev>"

        record = {
            "provider_message_id": provider_message_id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "from": email.from_address,
            "to": email.to_addresses,
            "cc": email.cc_addresses,
            "subject": email.subject,
            "text_body": email.text_body,
            "html_body": email.html_body,
            "in_reply_to": email.in_reply_to,
            "references": email.references,
        }
        DevelopmentEmailProvider._sent_log.append(record)

        logger.info(
            "DevelopmentEmailProvider: simulated send to=%s subject=%r message_id=%s",
            email.to_addresses, email.subject, provider_message_id,
        )

        return SendResult(success=True, provider_message_id=provider_message_id)

    @classmethod
    def get_sent_log(cls) -> list[dict]:
        return list(reversed(cls._sent_log))

    @classmethod
    def clear_sent_log(cls) -> None:
        cls._sent_log.clear()