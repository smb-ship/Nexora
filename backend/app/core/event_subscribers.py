import logging

from sqlalchemy.orm import Session

from app.core.events import event_bus, Event, EventType
from app.workflows.engine import run_workflows
from app.workflows.enums import WorkflowTriggerType
from app.models.event_log import EventLog

logger = logging.getLogger(__name__)

_WORKFLOW_MIRRORED_EVENTS = {
    EventType.TICKET_CREATED,
    EventType.TICKET_STATUS_CHANGED,
    EventType.TICKET_PRIORITY_CHANGED,
    EventType.TICKET_ASSIGNED,
    EventType.TICKET_UNASSIGNED,
    EventType.TICKET_COMMENT_ADDED,
    EventType.TICKET_SENTIMENT_CHANGED,
    EventType.TICKET_IDLE,
}


def _run_workflow_engine(db: Session, event: Event) -> None:
    ticket = event.payload.get("ticket")
    if ticket is None:
        logger.warning(
            "Event %s has no ticket in payload; workflow engine subscriber skipped (event_id=%s)",
            event.type.value, event.id,
        )
        return
    trigger_type = WorkflowTriggerType(event.type.value)
    run_workflows(db, trigger_type, ticket)


def _log_event(db: Session, event: Event) -> None:
    """Global subscriber (Step 7): persists every event for the Automation
    Dashboard's Event Feed. Uses its own commit so a logging failure can
    never roll back whatever the emitting request already committed."""
    log = EventLog(
        event_id=event.id,
        organization_id=event.organization_id,
        event_type=event.type.value,
        data=event.payload.get("data", {}),
    )
    db.add(log)
    db.commit()


def register_subscribers() -> None:
    for event_type in _WORKFLOW_MIRRORED_EVENTS:
        event_bus.subscribe(event_type, _run_workflow_engine)

    event_bus.subscribe_all(_log_event)

    # Webhook dispatch subscriber, added in Step 8.
    from app.webhooks.dispatcher import dispatch_to_webhooks
    event_bus.subscribe_all(dispatch_to_webhooks)

    logger.info(
        "Event subscribers registered: workflow engine -> %d event types, "
        "plus global event-log and webhook-dispatch subscribers",
        len(_WORKFLOW_MIRRORED_EVENTS),
    )