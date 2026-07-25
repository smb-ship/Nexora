from app.models.email import EmailInbox, EmailProviderType
from app.email.providers.base import EmailProvider
from app.email.providers.development import DevelopmentEmailProvider


class EmailProviderError(Exception):
    """Raised when no usable provider can be constructed for an inbox."""


def get_email_provider(inbox: EmailInbox) -> EmailProvider:
    """Provider factory — mirrors app/ai/providers/factory.py's
    get_ai_provider(). Adding SMTP/Gmail/SES later means adding one branch
    here and one new provider class; nothing else in the codebase changes."""
    if inbox.provider_type == EmailProviderType.DEVELOPMENT:
        return DevelopmentEmailProvider()

    # Future providers plug in here, e.g.:
    # if inbox.provider_type == EmailProviderType.SMTP:
    #     return SMTPEmailProvider(inbox.provider_config)

    raise EmailProviderError(
        f"No provider implementation available for '{inbox.provider_type.value}' yet. "
        f"Only 'development' is implemented in this milestone."
    )