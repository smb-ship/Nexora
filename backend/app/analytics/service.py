from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.analytics import calculators as calc
from app.analytics.filters import AnalyticsFilters
from app.models.ticket import Ticket
from app.schemas.analytics import DashboardMetrics, ChartsBundle, WorkflowStats


class AnalyticsService:
    """Aggregates ticket/workflow/AI data into dashboard metrics and chart
    series. Contains no route-handling or serialization-format concerns —
    those live in the router and export helpers respectively."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def dashboard_metrics(self, filters: AnalyticsFilters) -> DashboardMetrics:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        wf = calc.workflow_execution_stats(self._db, filters)

        return DashboardMetrics(
            total_tickets=calc.total_tickets(self._db, filters),
            open_tickets=calc.open_tickets(self._db, filters),
            closed_tickets=calc.closed_tickets(self._db, filters),
            tickets_today=calc.tickets_created_since(self._db, filters, today_start),
            tickets_this_week=calc.tickets_created_since(self._db, filters, week_start),
            tickets_this_month=calc.tickets_created_since(self._db, filters, month_start),
            avg_resolution_seconds=calc.avg_resolution_seconds(self._db, filters),
            avg_first_response_seconds=calc.avg_first_response_seconds(self._db, filters),
            avg_reply_seconds=calc.avg_reply_seconds(self._db, filters),
            ai_analyses_performed=calc.ai_analyses_performed(self._db, filters),
            workflow_stats=WorkflowStats(**wf),
        )

    def charts_bundle(self, filters: AnalyticsFilters) -> ChartsBundle:
        return ChartsBundle(
            tickets_by_priority=calc.tickets_by_priority(self._db, filters),
            tickets_by_status=calc.tickets_by_status(self._db, filters),
            tickets_by_source=calc.tickets_by_source(self._db, filters),
            tickets_by_team=calc.tickets_by_team(self._db, filters),
            tickets_by_agent=calc.tickets_by_agent(self._db, filters),
            sentiment_distribution=calc.sentiment_distribution(self._db, filters),
            daily_tickets=calc.daily_ticket_counts(self._db, filters),
        )

    def export_tickets(self, filters: AnalyticsFilters, fmt: str) -> tuple[str, str, str]:
        """Returns (content, media_type, filename) for filtered ticket rows.
        Row-level export, not the aggregated metrics — this is what
        'export filtered analytics' means in practice: the underlying data
        behind whatever filters are currently applied."""
        stmt = calc._apply_filters(
            __import__("sqlalchemy").select(Ticket), filters
        ).order_by(Ticket.created_at.desc())
        tickets = self._db.execute(stmt).scalars().all()

        rows = [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status.value,
                "priority": t.priority.value,
                "source": t.source.value,
                "requester_email": t.requester_email,
                "assigned_to": str(t.assigned_to) if t.assigned_to else "",
                "team_id": str(t.team_id) if t.team_id else "",
                "created_at": t.created_at.isoformat(),
                "closed_at": t.closed_at.isoformat() if t.closed_at else "",
            }
            for t in tickets
        ]

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        if fmt == "json":
            return json.dumps(rows, indent=2), "application/json", f"nexora-analytics-{stamp}.json"

        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return buf.getvalue(), "text/csv", f"nexora-analytics-{stamp}.csv"