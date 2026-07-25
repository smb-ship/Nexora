import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.workflows.enums import (
    WorkflowTriggerType,
    WorkflowConditionField,
    WorkflowOperator,
    WorkflowActionType,
    ConditionLogic,
)


class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    trigger_type: Mapped[WorkflowTriggerType] = mapped_column(
        SAEnum(WorkflowTriggerType, name="workflow_trigger_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    condition_logic: Mapped[ConditionLogic] = mapped_column(
        SAEnum(ConditionLogic, name="workflow_condition_logic", values_callable=lambda e: [m.value for m in e]),
        default=ConditionLogic.ALL,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    run_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    conditions = relationship(
        "WorkflowCondition", back_populates="rule", cascade="all, delete-orphan", order_by="WorkflowCondition.order"
    )
    actions = relationship(
        "WorkflowAction", back_populates="rule", cascade="all, delete-orphan", order_by="WorkflowAction.order"
    )


class WorkflowCondition(Base):
    __tablename__ = "workflow_conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_rules.id"), nullable=False)

    field: Mapped[WorkflowConditionField] = mapped_column(
        SAEnum(WorkflowConditionField, name="workflow_condition_field", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    operator: Mapped[WorkflowOperator] = mapped_column(
        SAEnum(WorkflowOperator, name="workflow_operator", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rule = relationship("WorkflowRule", back_populates="conditions")


class WorkflowAction(Base):
    __tablename__ = "workflow_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_rules.id"), nullable=False)

    action_type: Mapped[WorkflowActionType] = mapped_column(
        SAEnum(WorkflowActionType, name="workflow_action_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rule = relationship("WorkflowRule", back_populates="actions")


class WorkflowExecutionLog(Base):
    __tablename__ = "workflow_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_rules.id"), nullable=False)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)

    trigger_type: Mapped[WorkflowTriggerType] = mapped_column(
        SAEnum(
            WorkflowTriggerType,
            name="workflow_trigger_type",
            create_type=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    rule = relationship("WorkflowRule")
    ticket = relationship("Ticket")