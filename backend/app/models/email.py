import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class EmailProviderType(str, enum.Enum):
    DEVELOPMENT = "development"
    SMTP = "smtp"
    IMAP = "imap"
    GMAIL = "gmail"
    MICROSOFT365 = "microsoft365"
    SENDGRID = "sendgrid"
    AMAZON_SES = "amazon_ses"
    MAILGUN = "mailgun"


class EmailStatus(str, enum.Enum):
    RECEIVED = "received"   # inbound message, stored as-is
    PENDING = "pending"     # outbound, queued to send
    SENT = "sent"           # outbound, provider accepted it
    FAILED = "failed"       # outbound, provider rejected / send raised


class EmailInbox(Base):
    """A configured mailbox (e.g. support@acme.com) belonging to an
    organization. Deliberately its own table (not flat columns on Ticket)
    so an org can have multiple inboxes later (Known Technical Debt covers
    what's still needed for true multi-inbox support)."""

    __tablename__ = "email_inboxes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    email_address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    provider_type: Mapped[EmailProviderType] = mapped_column(
        SAEnum(EmailProviderType, name="email_provider_type", values_callable=lambda e: [m.value for m in e]),
        default=EmailProviderType.DEVELOPMENT,
        nullable=False,
    )
    # Provider-specific settings (SMTP host/port, API keys, OAuth refresh
    # tokens later) live here rather than as dedicated columns, so adding a
    # new provider never requires a migration — just a new key shape this
    # provider's config() reads.
    provider_config: Mapped[dict] = mapped_column(
        "provider_config", type_=__import__("sqlalchemy").dialects.postgresql.JSONB, default=dict, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class EmailAttachment(Base):
    """Metadata only — no file bytes stored here. storage_key is a
    placeholder for wherever a future storage provider (S3, local disk,
    etc.) would put the actual file; this table doesn't care which."""

    __tablename__ = "email_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticket_comments.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    comment = relationship("TicketComment", foreign_keys=[comment_id])