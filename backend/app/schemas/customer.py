import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str = Field(min_length=8)


class CustomerListItem(BaseModel):
    """Enriched list-row shape. total_tickets/open_tickets/last_seen are
    computed via a single grouped query in the router — never per-row
    lookups — see list_customers()'s docstring for the exact strategy."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    total_tickets: int
    open_tickets: int
    last_seen: datetime | None


class PaginatedCustomers(BaseModel):
    items: list[CustomerListItem]
    total: int
    skip: int
    limit: int


class CustomerStatsOut(BaseModel):
    lifetime_tickets: int
    open_issues: int
    resolution_rate: float | None  # resolved+closed / total, None if zero tickets
    avg_response_seconds: float | None  # ticket.created_at -> first public staff comment; None if no data


class CustomerDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    stats: CustomerStatsOut


class CustomerTicketOut(BaseModel):
    id: uuid.UUID
    subject: str
    status: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerChatSummaryOut(BaseModel):
    """Summary only — the frontend reuses the existing GET
    /chat/conversations/{id} endpoint (services/chat.ts) to fetch full
    messages when a conversation is expanded, rather than this router
    duplicating that query."""
    id: uuid.UUID
    status: str
    created_at: datetime
    message_count: int


class CustomerNoteCreate(BaseModel):
    body: str = Field(min_length=1)


class CustomerNoteUpdate(BaseModel):
    body: str = Field(min_length=1)


class CustomerNoteOut(BaseModel):
    id: uuid.UUID
    body: str
    author_id: uuid.UUID
    author_name: str | None
    created_at: datetime
    updated_at: datetime


class TimelineItemOut(BaseModel):
    """type: 'ticket_created' | 'chat_started' | 'note_added' |
    'automation_triggered' | 'event'. `data` carries just enough for the
    frontend to render one line + a link (e.g. ticket id + subject)."""
    type: str
    timestamp: datetime
    data: dict