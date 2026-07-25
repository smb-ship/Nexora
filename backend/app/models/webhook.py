import uuid
import enum
import secrets
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


def generate_signing_secret() -> str:
    return f"whsec_{secrets.token_urlsafe(32)}"


class OutgoingWebhook(Base):
    """An org-configured subscription: 'send these event types to this URL'.
    event_types stores EventType.value strings (not a Postgres enum array) so
    adding a new EventType later never requires a migration to alter this
    column — validated at the Pydantic schema layer instead."""

    __tablename__ = "outgoing_webhooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    event_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    signing_secret: Mapped[str] = mapped_column(String(255), nullable=False, default=generate_signing_secret)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Distinguishes dashboard-labeled integration type; purely cosmetic for
    # Phase F's "Connected Services" view — dispatch logic doesn't branch on
    # this. "generic" covers anything without a dedicated Phase E provider.
    integration_type: Mapped[str] = mapped_column(String(50), default="generic", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    delivery_logs = relationship(
        "WebhookDeliveryLog", back_populates="webhook", cascade="all, delete-orphan",
        order_by="WebhookDeliveryLog.created_at.desc()",
    )


class WebhookDeliveryLog(Base):
    """One row per delivery attempt group (not per individual HTTP retry —
    attempt_count tracks how many HTTP attempts happened within this one
    logical delivery). Kept indefinitely for the dashboard; pruning is
    listed as technical debt in the final SAVE PROGRESS."""

    __tablename__ = "webhook_delivery_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outgoing_webhooks.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        SAEnum(WebhookDeliveryStatus, name="webhook_delivery_status", values_callable=lambda e: [m.value for m in e]),
        default=WebhookDeliveryStatus.PENDING, nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    webhook = relationship("OutgoingWebhook", back_populates="delivery_logs")