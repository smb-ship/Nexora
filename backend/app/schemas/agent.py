import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AgentMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentChatResponse(BaseModel):
    message: AgentMessageOut
    tool_trace: list[dict] = []


class AgentConversationOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True