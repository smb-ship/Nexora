from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy import func, select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketSource
from app.models.chat import ChatConversation, ChatConversationStatus
from app.models.knowledge import KnowledgeArticle, ArticleStatus
from app.models.workflow import WorkflowRule
from app.models.event_log import EventLog
from app.analytics.filters import AnalyticsFilters
from app.analytics.service import AnalyticsService
from app.schemas.analytics import DashboardMetrics, ChartsBundle
from app.schemas.dashboard import DashboardSummary, DashboardCounts, RecentTicketOut, RecentEventOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    # Assumption flagged for you: no Permission.ANALYTICS_VIEW was in the
    # files I saw. Swap this for require_permission(Permission.ANALYTICS_VIEW)
    # if/when that exists — same pattern as the tickets router.
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    return current_user


def _filters_from_query(
    current_user: User,
    range: str | None,
    date_from: date | None,
    date_to: date | None,
    team_id: uuid.UUID | None,
    agent_id: uuid.UUID | None,
    priority: TicketPriority | None,
    status: TicketStatus | None,
    source: TicketSource | None,
) -> AnalyticsFilters:
    return AnalyticsFilters.from_query(
        current_user.organization_id,
        range_=range,
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        agent_id=agent_id,
        priority=priority,
        status=status,
        source=source,
    )


@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard(
    range: str | None = Query(None, pattern="^(today|7d|30d)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    agent_id: uuid.UUID | None = Query(None),
    priority: TicketPriority | None = Query(None),
    status: TicketStatus | None = Query(None),
    source: TicketSource | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    filters = _filters_from_query(current_user, range, date_from, date_to, team_id, agent_id, priority, status, source)
    return AnalyticsService(db).dashboard_metrics(filters)


@router.get("/charts", response_model=ChartsBundle)
def get_charts(
    range: str | None = Query(None, pattern="^(today|7d|30d)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    agent_id: uuid.UUID | None = Query(None),
    priority: TicketPriority | None = Query(None),
    status: TicketStatus | None = Query(None),
    source: TicketSource | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    filters = _filters_from_query(current_user, range, date_from, date_to, team_id, agent_id, priority, status, source)
    return AnalyticsService(db).charts_bundle(filters)


@router.get("/export")
def export_analytics(
    format: str = Query("csv", pattern="^(csv|json)$"),
    range: str | None = Query(None, pattern="^(today|7d|30d)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    team_id: uuid.UUID | None = Query(None),
    agent_id: uuid.UUID | None = Query(None),
    priority: TicketPriority | None = Query(None),
    status: TicketStatus | None = Query(None),
    source: TicketSource | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    filters = _filters_from_query(current_user, range, date_from, date_to, team_id, agent_id, priority, status, source)
    content, media_type, filename = AnalyticsService(db).export_tickets(filters, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
    
@router.get("/dashboard-summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Composed endpoint for the Dashboard page. Deliberately reuses
    AnalyticsService's existing methods rather than re-querying ticket
    aggregates — see DashboardSummary's docstring. Only genuinely new
    queries here are chat/KB/workflow counts, recent tickets, recent
    events, none of which AnalyticsService already computes."""
    org_id = current_user.organization_id
    filters = AnalyticsFilters.from_query(org_id)
    service = AnalyticsService(db)

    metrics = service.dashboard_metrics(filters)
    charts = service.charts_bundle(filters)

    live_chat_count = db.execute(
        select(func.count()).select_from(ChatConversation).where(
            ChatConversation.organization_id == org_id,
            ChatConversation.status == ChatConversationStatus.OPEN,
        )
    ).scalar_one()

    kb_published_count = db.execute(
        select(func.count()).select_from(KnowledgeArticle).where(
            KnowledgeArticle.organization_id == org_id,
            KnowledgeArticle.status == ArticleStatus.PUBLISHED,
        )
    ).scalar_one()

    workflows_active = db.execute(
        select(func.count()).select_from(WorkflowRule).where(
            WorkflowRule.organization_id == org_id, WorkflowRule.is_active.is_(True),
        )
    ).scalar_one()
    workflows_total = db.execute(
        select(func.count()).select_from(WorkflowRule).where(WorkflowRule.organization_id == org_id)
    ).scalar_one()

    counts = DashboardCounts(
        live_chat_conversations=live_chat_count,
        knowledge_articles_published=kb_published_count,
        automation_workflows_active=workflows_active,
        automation_workflows_total=workflows_total,
    )

    recent_tickets_rows = db.execute(
        select(Ticket).where(Ticket.organization_id == org_id)
        .order_by(Ticket.created_at.desc()).limit(8)
    ).scalars().all()

    recent_tickets = [
        RecentTicketOut(
            id=t.id, subject=t.subject, status=t.status.value, priority=t.priority.value,
            requester_name=t.requester_name,
            assigned_to_name=t.assignee.full_name if t.assignee else None,
            created_at=t.created_at,
        )
        for t in recent_tickets_rows
    ]

    recent_event_rows = db.execute(
        select(EventLog).where(EventLog.organization_id == org_id)
        .order_by(EventLog.created_at.desc()).limit(10)
    ).scalars().all()

    recent_events = [
        RecentEventOut(event_id=e.event_id, event_type=e.event_type, created_at=e.created_at, data=e.data)
        for e in recent_event_rows
    ]

    return DashboardSummary(
        metrics=metrics, charts=charts, counts=counts,
        recent_tickets=recent_tickets, recent_events=recent_events,
    )