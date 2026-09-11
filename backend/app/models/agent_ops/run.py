import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AgentRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(Base):
    """One invocation of the staff-facing Support Operations Agent - the
    audit trail the product spec calls for. Deliberately separate from
    AgentConversation (app.models.agent_conversation), which is the
    customer chatbot's turn-by-turn message log: a run is a single task a
    staff member handed the ops agent, not an ongoing back-and-forth."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Fixed to "support_operations" for now (spec: "start with one primary
    # agent"). Kept as a plain string rather than an enum so a future
    # specialized agent (Triage, Knowledge, ...) doesn't need a migration.
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, default="support_operations")

    status: Mapped[AgentRunStatus] = mapped_column(
        SAEnum(AgentRunStatus, name="agent_run_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False, default=AgentRunStatus.RUNNING,
    )

    initial_request: Mapped[str] = mapped_column(Text, nullable=False)
    # Human-readable label of what the agent is doing right now (e.g. "Searching
    # knowledge base..."). Milestone 9's dashboard polls this for a live run.
    # Currently only set at start/finish - see run_service's known limitation.
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    final_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    actions = relationship(
        "AgentAction", back_populates="run", cascade="all, delete-orphan", order_by="AgentAction.sequence",
    )