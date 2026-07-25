import logging
import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EventType(str, enum.Enum):
    """Every event Nexora's automation layer (workflows, webhooks, n8n) can
    react to. Ticket-shaped members intentionally mirror
    app.workflows.enums.WorkflowTriggerType 1:1 so the workflow engine can be
    driven purely off this bus without a translation table. Non-ticket
    members (EMAIL_*, AI_*, CUSTOMER_*, WORKFLOW_EXECUTED) exist for webhook
    subscribers only — the workflow engine never subscribes to these."""

    # Mirrors WorkflowTriggerType exactly
    TICKET_CREATED = "ticket_created"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_PRIORITY_CHANGED = "ticket_priority_changed"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_UNASSIGNED = "ticket_unassigned"
    TICKET_COMMENT_ADDED = "ticket_comment_added"
    TICKET_SENTIMENT_CHANGED = "ticket_sentiment_changed"
    TICKET_IDLE = "ticket_idle"

    # Non-workflow events (webhook / n8n / dashboard consumers only)
    EMAIL_RECEIVED = "email_received"
    EMAIL_SENT = "email_sent"
    AI_COMPLETED = "ai_completed"
    CUSTOMER_CREATED = "customer_created"
    WORKFLOW_EXECUTED = "workflow_executed"


@dataclass
class Event:
    """The payload passed to every subscriber. `payload` is a plain dict —
    subscribers that need a real ORM object (like the workflow engine) pull
    it via `payload["ticket"]`; subscribers that only need serializable data
    (webhooks, n8n) use `to_public_dict()`, which excludes ORM objects."""

    id: uuid.UUID
    type: EventType
    organization_id: uuid.UUID
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_public_dict(self) -> dict[str, Any]:
        """Serializable view for webhook bodies / n8n payloads. Any ORM
        instances in `payload` are dropped here — webhook subscribers should
        read from `payload["data"]` (a plain dict) rather than
        `payload["ticket"]` (an ORM object)."""
        return {
            "event_id": str(self.id),
            "event_type": self.type.value,
            "organization_id": str(self.organization_id),
            "created_at": self.created_at.isoformat(),
            "data": self.payload.get("data", {}),
        }


EventHandler = Callable[[Session, Event], None]


class EventBus:
    """Process-local synchronous pub/sub. Subscribers run in-order, in the
    same DB transaction/session as the emitting request. A failing
    subscriber is caught and logged — one bad webhook or n8n forward must
    never break ticket creation, exactly like run_workflows already
    isolates bad workflow rules from each other."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventHandler]] = {}
        self._global_subscribers: list[EventHandler] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Registers a handler that runs on every event, regardless of
        type — used for event logging (Step 7) and webhook dispatch
        (Step 8), both of which need to inspect event.type themselves
        rather than being registered per-type like the workflow engine."""
        self._global_subscribers.append(handler)

    def emit(self, db: Session, event: Event) -> None:
        for handler in self._global_subscribers:
            try:
                handler(db, event)
            except Exception:
                logger.exception(
                    "Global event subscriber %s failed for event %s (%s)",
                    getattr(handler, "__name__", handler), event.type.value, event.id,
                )

        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler(db, event)
            except Exception:
                logger.exception(
                    "Event subscriber %s failed for event %s (%s)",
                    getattr(handler, "__name__", handler),
                    event.type.value,
                    event.id,
                )


# Single process-wide bus instance. Subscribers register themselves at
# import time via app/core/event_subscribers.py (wired in Step 2).
event_bus = EventBus()


def emit_event(
    db: Session,
    event_type: EventType,
    organization_id: uuid.UUID,
    *,
    ticket: Any | None = None,
    data: dict[str, Any] | None = None,
) -> Event:
    """Convenience entrypoint for call-sites. `ticket` (an ORM object, or
    None) is what workflow-engine subscribers consume; `data` is a plain
    JSON-safe dict for webhook/n8n subscribers. Both can be set at once —
    e.g. a ticket-created event passes both `ticket=ticket` (for the
    workflow engine) and `data={...}` (for webhooks)."""
    event = Event(
        id=uuid.uuid4(),
        type=event_type,
        organization_id=organization_id,
        payload={"ticket": ticket, "data": data or {}},
    )
    event_bus.emit(db, event)
    return event