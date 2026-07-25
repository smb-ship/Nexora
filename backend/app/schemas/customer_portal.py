import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.ticket import TicketStatus, TicketPriority, TicketCategory

# Customers may not self-escalate to URGENT — that's reserved for staff/AI
# escalation. Anything outside this set silently falls back to MEDIUM rather
# than rejecting the request outright, since it's a policy default, not a
# data-integrity concern.
ALLOWED_CUSTOMER_PRIORITIES = {TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH}


class CustomerTicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    category: TicketCategory = TicketCategory.GENERAL
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator("priority")
    @classmethod
    def restrict_priority(cls, v: TicketPriority) -> TicketPriority:
        if v not in ALLOWED_CUSTOMER_PRIORITIES:
            return TicketPriority.MEDIUM
        return v


class CustomerAgentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str | None


class CustomerTicketListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    created_at: datetime
    updated_at: datetime
    assignee: CustomerAgentSummary | None = None


class CustomerTicketDetail(CustomerTicketListItem):
    description: str


class CustomerTicketListResponse(BaseModel):
    items: list[CustomerTicketListItem]
    total: int
    skip: int
    limit: int


class CustomerCommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CustomerCommentOut(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    author_id: uuid.UUID
    is_own_message: bool


class CustomerDashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    closed_tickets: int
    recent_tickets: list[CustomerTicketListItem]