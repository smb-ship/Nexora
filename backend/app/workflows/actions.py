import uuid
import logging

from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketComment
from app.models.workflow import WorkflowAction, WorkflowRule
from app.workflows.enums import WorkflowActionType

logger = logging.getLogger(__name__)


class WorkflowActionError(Exception):
    """Raised when a workflow action cannot be applied (bad params, invalid target, etc.)."""


def _execute_assign_team(db: Session, ticket: Ticket, params: dict) -> str:
    team_id = params.get("team_id")
    if not team_id:
        raise WorkflowActionError("assign_team action is missing 'team_id'")
    try:
        ticket.team_id = uuid.UUID(str(team_id))
    except ValueError as exc:
        raise WorkflowActionError(f"assign_team: '{team_id}' is not a valid UUID") from exc
    return f"Assigned team {team_id}"


def _execute_assign_user(db: Session, ticket: Ticket, params: dict) -> str:
    user_id = params.get("user_id")
    if not user_id:
        raise WorkflowActionError("assign_user action is missing 'user_id'")
    try:
        ticket.assigned_to = uuid.UUID(str(user_id))
    except ValueError as exc:
        raise WorkflowActionError(f"assign_user: '{user_id}' is not a valid UUID") from exc
    return f"Assigned user {user_id}"


def _execute_unassign(db: Session, ticket: Ticket, params: dict) -> str:
    ticket.assigned_to = None
    return "Unassigned ticket"


def _execute_set_priority(db: Session, ticket: Ticket, params: dict) -> str:
    priority = params.get("priority")
    if not priority:
        raise WorkflowActionError("set_priority action is missing 'priority'")
    try:
        ticket.priority = TicketPriority(priority)
    except ValueError as exc:
        raise WorkflowActionError(f"set_priority: '{priority}' is not a valid priority") from exc
    return f"Set priority to {priority}"


def _execute_set_status(db: Session, ticket: Ticket, params: dict) -> str:
    status = params.get("status")
    if not status:
        raise WorkflowActionError("set_status action is missing 'status'")
    try:
        ticket.status = TicketStatus(status)
    except ValueError as exc:
        raise WorkflowActionError(f"set_status: '{status}' is not a valid status") from exc
    return f"Set status to {status}"


def _execute_add_internal_note(db: Session, ticket: Ticket, params: dict, actor_user_id: uuid.UUID) -> str:
    message = params.get("message") or "Workflow automation note"
    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=actor_user_id,
        body=f"\U0001F916 Automation: {message}",
        is_internal_note=True,
    )
    db.add(comment)
    return "Added internal note"


_EXECUTORS = {
    WorkflowActionType.ASSIGN_TEAM: _execute_assign_team,
    WorkflowActionType.ASSIGN_USER: _execute_assign_user,
    WorkflowActionType.UNASSIGN: _execute_unassign,
    WorkflowActionType.SET_PRIORITY: _execute_set_priority,
    WorkflowActionType.SET_STATUS: _execute_set_status,
}


def execute_action(db: Session, ticket: Ticket, action: WorkflowAction, rule: WorkflowRule) -> str:
    if action.action_type == WorkflowActionType.ADD_INTERNAL_NOTE:
        return _execute_add_internal_note(db, ticket, action.params, rule.created_by)

    executor = _EXECUTORS.get(action.action_type)
    if executor is None:
        raise WorkflowActionError(f"Unknown action type: {action.action_type}")
    return executor(db, ticket, action.params)


def execute_actions(db: Session, ticket: Ticket, actions: list[WorkflowAction], rule: WorkflowRule) -> list[str]:
    return [execute_action(db, ticket, action, rule) for action in actions]