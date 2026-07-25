import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.ticket import TicketStatus, TicketPriority, TicketSource


class TicketCommentCreate(BaseModel):
    body: str
    is_internal_note: bool = False


class TicketCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    is_internal_note: bool
    created_at: datetime
    # --- Email integration (Milestone 8) ---
    is_email: bool = False
    email_status: str | None = None
    email_from: str | None = None


class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    requester_name: str
    requester_email: EmailStr
    assigned_to: uuid.UUID | None = None
    team_id: uuid.UUID | None = None


class TicketUpdate(BaseModel):
    subject: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to: uuid.UUID | None = None
    team_id: uuid.UUID | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    requester_name: str
    requester_email: str
    created_by: uuid.UUID
    assigned_to: uuid.UUID | None
    team_id: uuid.UUID | None
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    unread: bool = False
    # --- Email integration / Unified Inbox (Milestone 8, Phase E) ---
    source: TicketSource
    inbox_id: uuid.UUID | None
    email_thread_id: str | None
    # Computed, not a DB column — see _attach_reply_flags in tickets.py.
    # True = staff replied last (ball is in the customer's court).
    # False = customer's last message hasn't been answered yet.
    replied: bool = False


class TicketDetailOut(TicketOut):
    comments: list[TicketCommentOut] = []


class InboxCounts(BaseModel):
    mine: int
    unassigned: int
    all_open: int
    unread: int