import uuid
import hashlib
import secrets
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


def generate_key() -> tuple[str, str]:
    """Returns (plaintext_key, sha256_hash). Plaintext is shown to the user
    exactly once at creation time (like a Stripe API key) — only the hash
    is ever stored, mirroring how JWT/password secrets are never stored
    in plaintext elsewhere in this codebase."""
    plaintext = f"nxk_{secrets.token_urlsafe(32)}"
    return plaintext, hashlib.sha256(plaintext.encode()).hexdigest()


class IncomingWebhookKey(Base):
    """An API key n8n (or any external caller) presents via the
    X-Nexora-Webhook-Key header to invoke POST /api/v1/integrations/incoming/*
    endpoints. Scoped to a single organization — never global."""

    __tablename__ = "incoming_webhook_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)