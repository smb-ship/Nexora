import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.workflows.enums import (
    WorkflowTriggerType,
    WorkflowConditionField,
    WorkflowOperator,
    WorkflowActionType,
    ConditionLogic,
)


class WorkflowConditionCreate(BaseModel):
    field: WorkflowConditionField
    operator: WorkflowOperator
    value: str | None = None
    order: int = 0


class WorkflowConditionOut(WorkflowConditionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class WorkflowActionCreate(BaseModel):
    action_type: WorkflowActionType
    params: dict = Field(default_factory=dict)
    order: int = 0


class WorkflowActionOut(WorkflowActionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class WorkflowRuleCreate(BaseModel):
    name: str
    description: str | None = None
    trigger_type: WorkflowTriggerType
    condition_logic: ConditionLogic = ConditionLogic.ALL
    is_active: bool = True
    run_order: int = 0
    conditions: list[WorkflowConditionCreate] = Field(default_factory=list)
    actions: list[WorkflowActionCreate] = Field(min_length=1)


class WorkflowRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: WorkflowTriggerType | None = None
    condition_logic: ConditionLogic | None = None
    is_active: bool | None = None
    run_order: int | None = None
    conditions: list[WorkflowConditionCreate] | None = None
    actions: list[WorkflowActionCreate] | None = None


class WorkflowRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    trigger_type: WorkflowTriggerType
    condition_logic: ConditionLogic
    is_active: bool
    run_order: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    conditions: list[WorkflowConditionOut]
    actions: list[WorkflowActionOut]


class WorkflowExecutionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    rule_id: uuid.UUID
    ticket_id: uuid.UUID
    trigger_type: WorkflowTriggerType
    success: bool
    error_message: str | None
    actions_summary: dict
    created_at: datetime