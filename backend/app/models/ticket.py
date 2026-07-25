import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, enum.Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class TicketSource(str, enum.Enum):
    """How the ticket originated. Existing rows default to WEB via the
    migration's server_default — nothing about the agent dashboard or
    customer portal changes because of this column existing."""
    WEB = "web"
    CUSTOMER_PORTAL = "customer_portal"
    EMAIL = "email"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus, name="ticket_status"), default=TicketStatus.OPEN, nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SAEnum(TicketPriority, name="ticket_priority"), default=TicketPriority.MEDIUM, nullable=False
    )
    category: Mapped[TicketCategory] = mapped_column(
        SAEnum(TicketCategory, name="ticket_category"), default=TicketCategory.GENERAL, nullable=False
    )
    source: Mapped[TicketSource] = mapped_column(
        SAEnum(TicketSource, name="ticket_source", values_callable=lambda e: [m.value for m in e]),
        default=TicketSource.WEB,
        nullable=False,
    )

    requester_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nullable as of Milestone 10: tickets created via an authenticated n8n
    # integration call have no staff User initiating them. Every prior
    # creation path (staff UI, customer portal, email) still always sets
    # this — only the new /integrations/incoming/create-ticket path leaves
    # it null.
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

    # Distinct from created_by: created_by is whoever logged the record (could
    # be staff on the customer's behalf); customer_id is who the ticket
    # belongs to, and is what the customer portal always filters on.
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # --- Email integration (Milestone 8) ---
    inbox_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("email_inboxes.id"), nullable=True)
    # Stable thread key used to attach future replies to this ticket without
    # re-deriving it from headers every time. Normalized from the first
    # inbound message's Message-ID (see workflows/threading.py in Phase C).
    email_thread_id: Mapped[str | None] = mapped_column(String(998), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    customer = relationship("User", foreign_keys=[customer_id])
    team = relationship("Team", foreign_keys=[team_id])
    inbox = relationship("EmailInbox", foreign_keys=[inbox_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal_note: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # --- Email integration (Milestone 8) ---
    # All nullable: a normal web/portal comment has none of these set.
    is_email: Mapped[bool] = mapped_column(default=False, nullable=False)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_message_id: Mapped[str | None] = mapped_column(String(998), unique=True, nullable=True)
    email_in_reply_to: Mapped[str | None] = mapped_column(String(998), nullable=True)
    email_references: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    email_from: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_to: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    email_cc: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    email_bcc: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    email_status: Mapped[str | None] = mapped_column(
        SAEnum("received", "pending", "sent", "failed", name="email_status"), nullable=True
    )

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    attachments = relationship("EmailAttachment", primaryjoin="TicketComment.id == EmailAttachment.comment_id", viewonly=True)