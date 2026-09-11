import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentRunRequest(BaseModel):
    message: str


class AgentActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence: int
    tool_name: str
    arguments: dict | None = None
    success: bool
    summary: str | None = None
    risk: str | None = None
    created_at: datetime


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_name: str
    status: str
    initial_request: str
    current_step: str | None = None
    final_result: str | None = None
    error: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    actions: list[AgentActionOut] = []


class AgentRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_name: str
    status: str
    initial_request: str
    started_at: datetime
    completed_at: datetime | None = None