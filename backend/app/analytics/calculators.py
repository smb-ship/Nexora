from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketComment, TicketStatus
from app.models.ticket_ai_insight import TicketAIInsight
from app.models.workflow import WorkflowRule, WorkflowExecutionLog
from app.models.team import Team
from app.models.user import User
from app.analytics.filters import AnalyticsFilters

OPEN_STATUSES = [TicketStatus.OPEN, TicketStatus.PENDING, TicketStatus.ON_HOLD]
CLOSED_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED]


def _apply_filters(stmt, filters: AnalyticsFilters):
    stmt = stmt.where(Ticket.organization_id == filters.organization_id)
    if filters.date_from:
        stmt = stmt.where(Ticket.created_at >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Ticket.created_at <= filters.date_to)
    if filters.team_id:
        stmt = stmt.where(Ticket.team_id == filters.team_id)
    if filters.agent_id:
        stmt = stmt.where(Ticket.assigned_to == filters.agent_id)
    if filters.priority:
        stmt = stmt.where(Ticket.priority == filters.priority)
    if filters.status:
        stmt = stmt.where(Ticket.status == filters.status)
    if filters.source:
        stmt = stmt.where(Ticket.source == filters.source)
    return stmt


def total_tickets(db: Session, filters: AnalyticsFilters) -> int:
    stmt = _apply_filters(select(func.count()).select_from(Ticket), filters)
    return db.execute(stmt).scalar_one()


def open_tickets(db: Session, filters: AnalyticsFilters) -> int:
    stmt = _apply_filters(select(func.count()).select_from(Ticket), filters).where(
        Ticket.status.in_(OPEN_STATUSES)
    )
    return db.execute(stmt).scalar_one()


def closed_tickets(db: Session, filters: AnalyticsFilters) -> int:
    stmt = _apply_filters(select(func.count()).select_from(Ticket), filters).where(
        Ticket.status.in_(CLOSED_STATUSES)
    )
    return db.execute(stmt).scalar_one()


def tickets_created_since(db: Session, filters: AnalyticsFilters, since: datetime) -> int:
    stmt = _apply_filters(select(func.count()).select_from(Ticket), filters).where(
        Ticket.created_at >= since
    )
    return db.execute(stmt).scalar_one()


def avg_resolution_seconds(db: Session, filters: AnalyticsFilters) -> float | None:
    stmt = _apply_filters(
        select(func.avg(func.extract("epoch", Ticket.closed_at - Ticket.created_at))), filters
    ).where(Ticket.closed_at.isnot(None))
    return db.execute(stmt).scalar_one()


def avg_first_response_seconds(db: Session, filters: AnalyticsFilters) -> float | None:
    """Average time between ticket creation and the first PUBLIC comment
    authored by someone other than the customer. Correlated subquery per
    ticket rather than a window function — easier to read, fine at current
    scale. Revisit if this becomes a hot path (see technical debt)."""
    first_staff_comment = (
        select(func.min(TicketComment.created_at))
        .where(
            TicketComment.ticket_id == Ticket.id,
            TicketComment.is_internal_note.is_(False),
            TicketComment.author_id != Ticket.customer_id,
        )
        .correlate(Ticket)
        .scalar_subquery()
    )
    stmt = _apply_filters(
        select(func.avg(func.extract("epoch", first_staff_comment - Ticket.created_at))), filters
    ).where(Ticket.customer_id.isnot(None))
    return db.execute(stmt).scalar_one()


def avg_reply_seconds(db: Session, filters: AnalyticsFilters) -> float | None:
    """Average gap between consecutive public comments where the author
    changes (i.e. any back-and-forth turnaround, not just staff replying to
    a customer). Uses LAG() over each ticket's comment timeline."""
    prev_created_at = func.lag(TicketComment.created_at).over(
        partition_by=TicketComment.ticket_id, order_by=TicketComment.created_at
    )
    prev_author = func.lag(TicketComment.author_id).over(
        partition_by=TicketComment.ticket_id, order_by=TicketComment.created_at
    )
    gaps = (
        select(
            TicketComment.ticket_id,
            func.extract("epoch", TicketComment.created_at - prev_created_at).label("gap"),
            prev_author.label("prev_author"),
            TicketComment.author_id.label("author_id"),
        )
        .where(TicketComment.is_internal_note.is_(False))
        .subquery()
    )
    stmt = (
        select(func.avg(gaps.c.gap))
        .select_from(gaps)
        .join(Ticket, Ticket.id == gaps.c.ticket_id)
        .where(gaps.c.prev_author.isnot(None), gaps.c.prev_author != gaps.c.author_id)
    )
    stmt = _apply_filters(stmt, filters)
    return db.execute(stmt).scalar_one()


def _group_count(db: Session, filters: AnalyticsFilters, column):
    stmt = _apply_filters(select(column, func.count()).select_from(Ticket), filters).group_by(column)
    rows = db.execute(stmt).all()
    return [{"key": key.value if hasattr(key, "value") else key, "count": count} for key, count in rows]


def tickets_by_priority(db: Session, filters: AnalyticsFilters):
    return _group_count(db, filters, Ticket.priority)


def tickets_by_status(db: Session, filters: AnalyticsFilters):
    return _group_count(db, filters, Ticket.status)


def tickets_by_source(db: Session, filters: AnalyticsFilters):
    return _group_count(db, filters, Ticket.source)


def tickets_by_team(db: Session, filters: AnalyticsFilters):
    stmt = _apply_filters(
        select(Team.name, func.count(Ticket.id)).select_from(Ticket).join(Team, Team.id == Ticket.team_id),
        filters,
    ).group_by(Team.name)
    return [{"key": name, "count": count} for name, count in db.execute(stmt).all()]


def tickets_by_agent(db: Session, filters: AnalyticsFilters):
    stmt = _apply_filters(
        select(User.full_name, User.id, func.count(Ticket.id))
        .select_from(Ticket)
        .join(User, User.id == Ticket.assigned_to),
        filters,
    ).group_by(User.id, User.full_name)
    return [{"key": name or str(uid), "count": count} for name, uid, count in db.execute(stmt).all()]


def daily_ticket_counts(db: Session, filters: AnalyticsFilters):
    day_bucket = func.date_trunc("day", Ticket.created_at)
    stmt = _apply_filters(select(day_bucket.label("day"), func.count()).select_from(Ticket), filters)
    stmt = stmt.group_by(day_bucket).order_by(day_bucket)
    return [{"date": d.date().isoformat(), "count": c} for d, c in db.execute(stmt).all()]


def sentiment_distribution(db: Session, filters: AnalyticsFilters):
    stmt = (
        select(TicketAIInsight.sentiment, func.count())
        .select_from(TicketAIInsight)
        .join(Ticket, Ticket.id == TicketAIInsight.ticket_id)
    )
    stmt = _apply_filters(stmt, filters).where(TicketAIInsight.sentiment.isnot(None))
    stmt = stmt.group_by(TicketAIInsight.sentiment)
    return [{"key": s.value, "count": c} for s, c in db.execute(stmt).all()]


def ai_analyses_performed(db: Session, filters: AnalyticsFilters) -> int:
    stmt = (
        select(func.count())
        .select_from(TicketAIInsight)
        .join(Ticket, Ticket.id == TicketAIInsight.ticket_id)
        .where(TicketAIInsight.generated_at.isnot(None))
    )
    return db.execute(_apply_filters(stmt, filters)).scalar_one()


def workflow_execution_stats(db: Session, filters: AnalyticsFilters) -> dict:
    """Not routed through _apply_filters/Ticket — execution logs are scoped
    to the org via their parent WorkflowRule, and filtered by their own
    created_at rather than Ticket.created_at."""
    stmt = (
        select(
            func.count(),
            func.sum(case((WorkflowExecutionLog.success.is_(True), 1), else_=0)),
        )
        .select_from(WorkflowExecutionLog)
        .join(WorkflowRule, WorkflowRule.id == WorkflowExecutionLog.rule_id)
        .where(WorkflowRule.organization_id == filters.organization_id)
    )
    if filters.date_from:
        stmt = stmt.where(WorkflowExecutionLog.created_at >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(WorkflowExecutionLog.created_at <= filters.date_to)
    total, succeeded = db.execute(stmt).one()
    total = total or 0
    succeeded = succeeded or 0
    rate = round((succeeded / total * 100), 1) if total else 0.0
    return {"total_executions": total, "successful_executions": succeeded, "success_rate": rate}