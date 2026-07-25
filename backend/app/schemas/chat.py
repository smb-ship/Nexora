import uuid
from datetime import datetime
from pydantic import BaseModel


class ChatSessionStart(BaseModel):
    name: str | None = None
    email: str | None = None


class ChatSessionOut(BaseModel):
    conversation_id: uuid.UUID
    visitor_id: uuid.UUID
    welcome_message: str


class ChatMessageCreate(BaseModel):
    body: str


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    sender_type: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationOut(BaseModel):
    id: uuid.UUID
    status: str
    assigned_to: uuid.UUID | None
    ticket_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatConversationDetailOut(ChatConversationOut):
    messages: list[ChatMessageOut]