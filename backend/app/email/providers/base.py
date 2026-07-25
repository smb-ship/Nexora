from abc import ABC, abstractmethod

from app.email.schemas import OutboundEmail, SendResult


class EmailProvider(ABC):
    """Abstract email provider — mirrors app/ai/providers/base.py's pattern.
    Every concrete provider (development, SMTP, Gmail, SES, ...) implements
    this interface; nothing above this layer ever imports a concrete
    provider directly."""

    @abstractmethod
    async def send(self, email: OutboundEmail) -> SendResult:
        """Send an outbound email. Must not raise for ordinary send
        failures — return SendResult(success=False, error=...) instead, so
        EmailService can log/retry uniformly. Raising is reserved for
        programmer errors (bad config), not delivery failures."""
        ...