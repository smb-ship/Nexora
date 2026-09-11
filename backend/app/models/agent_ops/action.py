import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class AgentAction(Base):
    """One tool call within an AgentRun - maps directly to one entry in
    the trace list AgentOrchestrator.run_turn() already returns
    (app/agent/orchestrator.py's AgentTurnResult.trace), persisted so the
    execution trace survives past the request/response cycle. No new
    tracing concept was invented here - this table just gives the
    orchestrator's existing trace format a permanent home."""

    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Snapshot of the tool's ToolRisk at call time (app.agent.security.tool_permissions),
    # stored as plain text since it's descriptive metadata for the UI, never filtered on.
    risk: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run = relationship("AgentRun", back_populates="actions")