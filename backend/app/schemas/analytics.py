from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel

from app.models.ticket import TicketPriority, TicketStatus, TicketSource


class AnalyticsQuery(BaseModel):
    range: str | None = None  # "today" | "7d" | "30d" | None (custom/all-time)
    date_from: date | None = None
    date_to: date | None = None
    team_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    source: TicketSource | None = None


class GroupCount(BaseModel):
    key: str
    count: int


class DailyCount(BaseModel):
    date: str
    count: int


class WorkflowStats(BaseModel):
    total_executions: int
    successful_executions: int
    success_rate: float


class DashboardMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    tickets_today: int
    tickets_this_week: int
    tickets_this_month: int
    avg_resolution_seconds: float | None
    avg_first_response_seconds: float | None
    avg_reply_seconds: float | None
    ai_analyses_performed: int
    workflow_stats: WorkflowStats


class ChartsBundle(BaseModel):
    tickets_by_priority: list[GroupCount]
    tickets_by_status: list[GroupCount]
    tickets_by_source: list[GroupCount]
    tickets_by_team: list[GroupCount]
    tickets_by_agent: list[GroupCount]
    sentiment_distribution: list[GroupCount]
    daily_tickets: list[DailyCount]