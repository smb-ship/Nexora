from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from app.models.ticket import TicketStatus, TicketPriority, TicketSource


@dataclass
class AnalyticsFilters:
    organization_id: uuid.UUID
    date_from: datetime | None = None
    date_to: datetime | None = None
    team_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    source: TicketSource | None = None

    @classmethod
    def from_query(
        cls,
        organization_id: uuid.UUID,
        *,
        range_: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        team_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
        priority: TicketPriority | None = None,
        status: TicketStatus | None = None,
        source: TicketSource | None = None,
    ) -> "AnalyticsFilters":
        resolved_from, resolved_to = _resolve_range(range_, date_from, date_to)
        return cls(
            organization_id=organization_id,
            date_from=resolved_from,
            date_to=resolved_to,
            team_id=team_id,
            agent_id=agent_id,
            priority=priority,
            status=status,
            source=source,
        )


def _resolve_range(
    range_: str | None, date_from: date | None, date_to: date | None
) -> tuple[datetime | None, datetime | None]:
    now = datetime.now(timezone.utc)
    if range_ == "today":
        return datetime.combine(now.date(), time.min, tzinfo=timezone.utc), now
    if range_ == "7d":
        return now - timedelta(days=7), now
    if range_ == "30d":
        return now - timedelta(days=30), now
    if date_from or date_to:
        start = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
        end = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
        return start, end
    return None, None  # all-time, no range filter applied