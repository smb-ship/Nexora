import uuid
from datetime import datetime
from pydantic import BaseModel

from app.schemas.analytics import DashboardMetrics, ChartsBundle


class DashboardCounts(BaseModel):
    """The three counts M9's AnalyticsService doesn't compute — chat,
    knowledge, and workflow-rule counts live outside the ticket-centric
    analytics domain, so they're queried fresh here rather than bolted
    onto AnalyticsService."""
    live_chat_conversations: int
    knowledge_articles_published: int
    automation_workflows_active: int
    automation_workflows_total: int


class RecentTicketOut(BaseModel):
    id: uuid.UUID
    subject: str
    status: str
    priority: str
    requester_name: str
    assigned_to_name: str | None
    created_at: datetime


class RecentEventOut(BaseModel):
    event_id: uuid.UUID
    event_type: str
    created_at: datetime
    # Kept minimal on purpose: the dashboard only needs enough of `data`
    # to render a one-line human description client-side (e.g. a ticket
    # subject or conversation id), not the full event payload.
    data: dict


class DashboardSummary(BaseModel):
    """Composed response for the Dashboard page. Reuses AnalyticsService's
    existing dashboard_metrics()/charts_bundle() output verbatim (no
    duplicated ticket-aggregation queries) and adds only the genuinely new
    pieces: chat/KB/workflow counts, recent tickets, recent events."""
    metrics: DashboardMetrics
    charts: ChartsBundle
    counts: DashboardCounts
    recent_tickets: list[RecentTicketOut]
    recent_events: list[RecentEventOut]