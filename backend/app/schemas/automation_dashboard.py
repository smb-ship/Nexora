import uuid
from datetime import datetime
from pydantic import BaseModel


class ConnectedServiceOut(BaseModel):
    id: uuid.UUID
    name: str
    integration_type: str
    target_url: str
    is_active: bool
    event_types: list[str]
    success_count: int
    failed_count: int
    last_delivery_at: datetime | None


class EventFeedItemOut(BaseModel):
    event_id: uuid.UUID
    event_type: str
    data: dict
    created_at: datetime


class AutomationDashboardOut(BaseModel):
    connected_services: list[ConnectedServiceOut]
    pending_retries: int
    deliveries_last_24h: int
    failures_last_24h: int
    recent_events: list[EventFeedItemOut]