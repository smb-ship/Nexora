import uuid
from datetime import datetime
from pydantic import BaseModel


class IncomingWebhookKeyCreate(BaseModel):
    name: str


class IncomingWebhookKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class IncomingWebhookKeyCreated(IncomingWebhookKeyOut):
    plaintext_key: str  # only ever present in the create response


class N8nCreateTicketRequest(BaseModel):
    subject: str
    description: str
    requester_name: str
    requester_email: str
    priority: str | None = None


class N8nAddCommentRequest(BaseModel):
    ticket_id: uuid.UUID
    body: str