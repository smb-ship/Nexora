import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AgentMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentConversation(Base):
    """A customer's ongoing chat with the AI agent. Deliberately separate
    from ChatConversation (the anonymous visitor<->staff live chat model) -
    this is always authenticated and always scoped to one logged-in
    customer, which ChatConversation/ChatVisitor has no concept of."""

    __tablename__ = "agent_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    customer = relationship("User", foreign_keys=[customer_id])
    messages = relationship(
        "AgentMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_conversations.id"), nullable=False)

    role: Mapped[AgentMessageRole] = mapped_column(
        SAEnum(AgentMessageRole, name="agent_message_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Visible text (user questions, final assistant answers). Null for an
    # assistant turn that only issued tool calls with no visible text.
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Only ever set on role=tool rows (Milestone 4 onward) - which tool ran
    # and with what arguments/result. Kept as JSON since this is an internal
    # reasoning trace, never queried or filtered on directly.
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tool_arguments: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    conversation = relationship("AgentConversation", back_populates="messages")