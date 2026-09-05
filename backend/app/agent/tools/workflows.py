import uuid

from sqlalchemy import select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.core.permissions import Permission
from app.models.ticket import Ticket
from app.models.workflow import WorkflowRule
from app.workflows.enums import WorkflowTriggerType


def _parse_uuid(raw) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


async def _get_workflow(args: dict, ctx: AgentToolContext) -> ToolResult:
    rule_id = _parse_uuid(args.get("rule_id"))
    if not rule_id:
        return ToolResult(success=False, summary="rule_id must be a valid UUID.")

    rule = ctx.db.get(WorkflowRule, rule_id)
    if not rule or rule.organization_id != ctx.organization_id:
        return ToolResult(success=False, summary="Workflow rule not found in this organization.")

    return ToolResult(
        success=True,
        summary=f"Found workflow rule '{rule.name}'.",
        data={
            "id": str(rule.id), "name": rule.name, "description": rule.description,
            "trigger_type": rule.trigger_type.value, "is_active": rule.is_active,
        },
    )


async def _list_workflows(args: dict, ctx: AgentToolContext) -> ToolResult:
    stmt = select(WorkflowRule).where(WorkflowRule.organization_id == ctx.organization_id)
    if args.get("is_active") is not None:
        stmt = stmt.where(WorkflowRule.is_active.is_(bool(args["is_active"])))
    stmt = stmt.order_by(WorkflowRule.run_order.asc())

    rules = ctx.db.execute(stmt).scalars().all()
    return ToolResult(
        success=True,
        summary=f"Found {len(rules)} workflow rule(s).",
        data={
            "rules": [
                {"id": str(r.id), "name": r.name, "trigger_type": r.trigger_type.value, "is_active": r.is_active}
                for r in rules
            ]
        },
    )


async def _trigger_workflow(args: dict, ctx: AgentToolContext) -> ToolResult:
    """HIGH RISK per the product spec ('trigger external workflow'). No
    human-approval path exists until Milestone 5, so this refuses to run
    rather than actually invoking app.workflows.engine.run_workflows.
    Still validates the ticket so the refusal message is meaningful."""
    ticket_id = _parse_uuid(args.get("ticket_id"))
    if not ticket_id:
        return ToolResult(success=False, summary="ticket_id must be a valid UUID.")

    ticket = ctx.db.get(Ticket, ticket_id)
    if not ticket or ticket.organization_id != ctx.organization_id:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    raw_trigger = args.get("trigger_type")
    try:
        WorkflowTriggerType(raw_trigger)
    except (ValueError, TypeError):
        return ToolResult(success=False, summary=f"'{raw_trigger}' is not a valid workflow trigger type.")

    return ToolResult(
        success=False,
        summary=(
            "Triggering a workflow is a high-risk action that requires human approval, "
            "which isn't implemented until Milestone 5. No workflow was run."
        ),
    )


def register(registry: AgentToolRegistry) -> None:
    registry.register(
        name="get_workflow",
        description="Get details of a single workflow automation rule by id.",
        parameters={
            "type": "object",
            "properties": {"rule_id": {"type": "string"}},
            "required": ["rule_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_workflow,
        required_permission=Permission.WORKFLOW_MANAGE,
    )
    registry.register(
        name="list_workflows",
        description="List this organization's workflow automation rules.",
        parameters={
            "type": "object",
            "properties": {"is_active": {"type": "boolean"}},
        },
        risk=ToolRisk.READ,
        executor=_list_workflows,
        required_permission=Permission.WORKFLOW_MANAGE,
    )
    registry.register(
        name="trigger_workflow",
        description=(
            "Manually run this organization's active workflow rules for a given trigger type against a ticket. "
            "High risk - currently requires human approval and will not execute."
        ),
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "trigger_type": {"type": "string", "enum": [t.value for t in WorkflowTriggerType]},
            },
            "required": ["ticket_id", "trigger_type"],
        },
        risk=ToolRisk.HIGH_RISK,
        executor=_trigger_workflow,
        required_permission=Permission.WORKFLOW_MANAGE,
    )