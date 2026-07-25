import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.ticket import Ticket, TicketStatus
from app.models.workflow import WorkflowRule, WorkflowExecutionLog
from app.workflows.conditions import evaluate_conditions
from app.workflows.actions import execute_actions, WorkflowActionError
from app.workflows.enums import WorkflowTriggerType

logger = logging.getLogger(__name__)


def run_workflows(db: Session, trigger_type: WorkflowTriggerType, ticket: Ticket) -> None:
    """Evaluate and execute all active workflow rules for a given trigger event
    against a single ticket. Commits any mutations made by matched rules.

    One bad rule (invalid params, unexpected error) never breaks the request —
    it's logged to workflow_execution_logs as a failure and the rest continue."""

    rules = (
        db.execute(
            select(WorkflowRule)
            .options(joinedload(WorkflowRule.conditions), joinedload(WorkflowRule.actions))
            .where(
                WorkflowRule.organization_id == ticket.organization_id,
                WorkflowRule.trigger_type == trigger_type,
                WorkflowRule.is_active.is_(True),
            )
            .order_by(WorkflowRule.run_order.asc())
        )
        .unique()
        .scalars()
        .all()
    )

    if not rules:
        return

    for rule in rules:
        try:
            matched = evaluate_conditions(db, ticket, rule.conditions, rule.condition_logic)
            if not matched:
                continue

            summaries = execute_actions(db, ticket, rule.actions, rule)

            db.add(
                WorkflowExecutionLog(
                    rule_id=rule.id,
                    ticket_id=ticket.id,
                    trigger_type=trigger_type,
                    success=True,
                    actions_summary={"actions": summaries},
                )
            )
        except WorkflowActionError as exc:
            logger.warning("Workflow rule %s failed for ticket %s: %s", rule.id, ticket.id, exc)
            db.add(
                WorkflowExecutionLog(
                    rule_id=rule.id, ticket_id=ticket.id, trigger_type=trigger_type,
                    success=False, error_message=str(exc), actions_summary={},
                )
            )
        except Exception as exc:  # defensive: a bad rule must never break the request
            logger.exception("Unexpected error running workflow rule %s", rule.id)
            db.add(
                WorkflowExecutionLog(
                    rule_id=rule.id, ticket_id=ticket.id, trigger_type=trigger_type,
                    success=False, error_message=f"Unexpected error: {exc}", actions_summary={},
                )
            )

    db.commit()
    db.refresh(ticket)


def run_idle_check(db: Session, organization_id: uuid.UUID) -> int:
    """Runs TICKET_IDLE rules against every open ticket in the org. Intended to
    be called periodically by an external scheduler (cron / APScheduler) —
    see the process-idle endpoint and Known Technical Debt below."""
    open_statuses = [TicketStatus.OPEN, TicketStatus.PENDING, TicketStatus.ON_HOLD]

    tickets = db.execute(
        select(Ticket).where(
            Ticket.organization_id == organization_id,
            Ticket.status.in_(open_statuses),
        )
    ).scalars().all()

    for ticket in tickets:
        run_workflows(db, WorkflowTriggerType.TICKET_IDLE, ticket)

    return len(tickets)