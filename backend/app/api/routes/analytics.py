from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.ticket import TicketPriority, TicketStatus, TicketSource
from app.analytics.filters import AnalyticsFilters
from app.analytics.service import AnalyticsService
from app.schemas.analytics import DashboardMetrics, ChartsBundle

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