from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_ai_insight import TicketAIInsight
from app.models.workflow import WorkflowCondition
from app.workflows.enums import WorkflowConditionField, WorkflowOperator, ConditionLogic


def _resolve_field_value(db: Session, ticket: Ticket, field: WorkflowConditionField):
    if field == WorkflowConditionField.STATUS:
        return ticket.status.value
    if field == WorkflowConditionField.PRIORITY:
        return ticket.priority.value
    if field == WorkflowConditionField.TEAM_ID:
        return str(ticket.team_id) if ticket.team_id else None
    if field == WorkflowConditionField.ASSIGNED_TO:
        return str(ticket.assigned_to) if ticket.assigned_to else None
    if field == WorkflowConditionField.IS_UNASSIGNED:
        return "true" if ticket.assigned_to is None else "false"
    if field == WorkflowConditionField.SUBJECT:
        return ticket.subject or ""
    if field == WorkflowConditionField.DESCRIPTION:
        return ticket.description or ""
    if field == WorkflowConditionField.HOURS_SINCE_UPDATED:
        updated_at = ticket.updated_at if ticket.updated_at.tzinfo else ticket.updated_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - updated_at).total_seconds() / 3600
    if field == WorkflowConditionField.HOURS_SINCE_CREATED:
        created_at = ticket.created_at if ticket.created_at.tzinfo else ticket.created_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    if field == WorkflowConditionField.SENTIMENT:
        insight = db.query(TicketAIInsight).filter(TicketAIInsight.ticket_id == ticket.id).one_or_none()
        return insight.sentiment.value if insight and insight.sentiment else None
    return None


def _apply_operator(operator: WorkflowOperator, actual, expected: str | None) -> bool:
    if operator == WorkflowOperator.IS_EMPTY:
        return actual is None or actual == ""
    if operator == WorkflowOperator.IS_NOT_EMPTY:
        return actual is not None and actual != ""

    if actual is None:
        return False

    if operator == WorkflowOperator.EQUALS:
        return str(actual).strip().lower() == str(expected or "").strip().lower()
    if operator == WorkflowOperator.NOT_EQUALS:
        return str(actual).strip().lower() != str(expected or "").strip().lower()
    if operator == WorkflowOperator.IN:
        choices = [v.strip().lower() for v in (expected or "").split(",")]
        return str(actual).strip().lower() in choices
    if operator == WorkflowOperator.CONTAINS:
        return str(expected or "").strip().lower() in str(actual).strip().lower()
    if operator == WorkflowOperator.GREATER_THAN:
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False
    if operator == WorkflowOperator.LESS_THAN:
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False
    return False


def evaluate_condition(db: Session, ticket: Ticket, condition: WorkflowCondition) -> bool:
    actual = _resolve_field_value(db, ticket, condition.field)
    return _apply_operator(condition.operator, actual, condition.value)


def evaluate_conditions(
    db: Session, ticket: Ticket, conditions: list[WorkflowCondition], logic: ConditionLogic
) -> bool:
    if not conditions:
        return True
    results = [evaluate_condition(db, ticket, c) for c in conditions]
    return all(results) if logic == ConditionLogic.ALL else any(results)