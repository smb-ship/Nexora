import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class SimulateInboundEmailRequest(BaseModel):
    """Dev-provider-only: lets you simulate an inbound email without a real
    mailbox, exercising the exact same process_inbound() pipeline a real
    webhook would call."""
    inbox_id: uuid.UUID
    from_address: EmailStr
    to_addresses: list[EmailStr] = Field(default_factory=list)
    subject: str
    text_body: str
    html_body: str | None = None
    in_reply_to: str | None = None
    references: list[str] = Field(default_factory=list)
    message_id: str | None = None  # auto-generated if omitted


class DevOutboxItem(BaseModel):
    provider_message_id: str
    sent_at: str
    from_address: str = Field(alias="from")
    to: list[str]
    cc: list[str]
    subject: str
    text_body: str
    html_body: str | None
    in_reply_to: str | None
    references: list[str]

    model_config = {"populate_by_name": True}


class EmailInboxCreate(BaseModel):
    email_address: EmailStr
    display_name: str
    provider_type: str = "development"


class EmailInboxOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email_address: str
    display_name: str
    provider_type: str
    is_active: bool
    created_at: datetime