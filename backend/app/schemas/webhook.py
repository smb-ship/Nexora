import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.core.events import EventType


class OutgoingWebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_url: str = Field(min_length=1, max_length=2048)
    event_types: list[str]
    integration_type: str = "generic"

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: list[str]) -> list[str]:
        valid = {e.value for e in EventType}
        invalid = [e for e in v if e not in valid]
        if invalid:
            raise ValueError(f"Unknown event type(s): {invalid}")
        if not v:
            raise ValueError("At least one event_type is required")
        return v


class OutgoingWebhookUpdate(BaseModel):
    name: str | None = None
    target_url: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None


class OutgoingWebhookOut(BaseModel):
    id: uuid.UUID
    name: str
    target_url: str
    event_types: list[str]
    integration_type: str
    is_active: bool
    signing_secret: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryLogOut(BaseModel):
    id: uuid.UUID
    webhook_id: uuid.UUID
    event_type: str
    event_id: uuid.UUID
    status: str
    attempt_count: int
    response_status_code: int | None
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None
    next_retry_at: datetime | None

    class Config:
        from_attributes = True