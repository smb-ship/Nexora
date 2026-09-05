import uuid

from sqlalchemy import or_, select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.security.validators import MAX_LONG_FIELD_LENGTH, check_text_length
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.core.permissions import Permission
from app.models.customer_note import CustomerNote
from app.models.ticket import Ticket
from app.models.user import User, UserRole


def _parse_uuid(raw, field_name: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


def _get_org_customer(ctx: AgentToolContext, customer_id: str) -> User | None:
    cid = _parse_uuid(customer_id, "customer_id")
    if not cid:
        return None
    customer = ctx.db.get(User, cid)
    if not customer or customer.organization_id != ctx.organization_id or customer.role != UserRole.CUSTOMER:
        return None
    return customer


def _customer_summary(c: User) -> dict:
    return {
        "id": str(c.id),
        "email": c.email,
        "full_name": c.full_name,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat(),
    }


async def _get_customer(args: dict, ctx: AgentToolContext) -> ToolResult:
    customer = _get_org_customer(ctx, args.get("customer_id"))
    if not customer:
        return ToolResult(success=False, summary="Customer not found in this organization.")
    return ToolResult(success=True, summary=f"Found customer {customer.email}.", data=_customer_summary(customer))


async def _search_customers(args: dict, ctx: AgentToolContext) -> ToolResult:
    query = (args.get("query") or "").strip()
    stmt = select(User).where(User.organization_id == ctx.organization_id, User.role == UserRole.CUSTOMER)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    limit = min(int(args.get("limit") or 10), 50)
    stmt = stmt.order_by(User.created_at.desc()).limit(limit)

    customers = ctx.db.execute(stmt).scalars().all()
    return ToolResult(
        success=True,
        summary=f"Found {len(customers)} customer(s).",
        data={"customers": [_customer_summary(c) for c in customers]},
    )


async def _get_customer_tickets(args: dict, ctx: AgentToolContext) -> ToolResult:
    customer = _get_org_customer(ctx, args.get("customer_id"))
    if not customer:
        return ToolResult(success=False, summary="Customer not found in this organization.")

    tickets = ctx.db.execute(
        select(Ticket).where(Ticket.customer_id == customer.id).order_by(Ticket.created_at.desc())
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"Customer has {len(tickets)} ticket(s).",
        data={
            "tickets": [
                {
                    "id": str(t.id), "subject": t.subject, "status": t.status.value,
                    "priority": t.priority.value, "created_at": t.created_at.isoformat(),
                }
                for t in tickets
            ]
        },
    )


async def _get_customer_history(args: dict, ctx: AgentToolContext) -> ToolResult:
    """Condensed timeline: recent tickets + staff notes. Deliberately
    lighter-weight than the /customers/{id}/timeline endpoint (which also
    pulls chat + workflow-execution rows) - enough for the agent to
    orient itself on a customer without an oversized tool result."""
    customer = _get_org_customer(ctx, args.get("customer_id"))
    if not customer:
        return ToolResult(success=False, summary="Customer not found in this organization.")

    limit = min(int(args.get("limit") or 10), 50)

    tickets = ctx.db.execute(
        select(Ticket).where(Ticket.customer_id == customer.id).order_by(Ticket.created_at.desc()).limit(limit)
    ).scalars().all()
    notes = ctx.db.execute(
        select(CustomerNote).where(CustomerNote.customer_id == customer.id)
        .order_by(CustomerNote.created_at.desc()).limit(limit)
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"{len(tickets)} recent ticket(s), {len(notes)} staff note(s).",
        data={
            "customer": _customer_summary(customer),
            "recent_tickets": [
                {"id": str(t.id), "subject": t.subject, "status": t.status.value, "created_at": t.created_at.isoformat()}
                for t in tickets
            ],
            "notes": [
                {"id": str(n.id), "body": n.body, "created_at": n.created_at.isoformat()}
                for n in notes
            ],
        },
    )


async def _add_customer_note(args: dict, ctx: AgentToolContext) -> ToolResult:
    customer = _get_org_customer(ctx, args.get("customer_id"))
    if not customer:
        return ToolResult(success=False, summary="Customer not found in this organization.")

    body = (args.get("body") or "").strip()
    if not body:
        return ToolResult(success=False, summary="body is required.")
    err = check_text_length(body, "body", MAX_LONG_FIELD_LENGTH)
    if err:
        return ToolResult(success=False, summary=err)

    note = CustomerNote(organization_id=ctx.organization_id, customer_id=customer.id, author_id=ctx.user.id, body=body)
    ctx.db.add(note)
    ctx.db.commit()
    ctx.db.refresh(note)

    return ToolResult(
        success=True, summary="Added a staff note to the customer's profile.",
        data={"note_id": str(note.id), "customer_id": str(customer.id), "created_at": note.created_at.isoformat()},
    )


def register(registry: AgentToolRegistry) -> None:
    registry.register(
        name="get_customer",
        description="Get a customer's profile by id.",
        parameters={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_customer,
        required_permission=Permission.CUSTOMER_MANAGE,
    )
    registry.register(
        name="search_customers",
        description="Search this organization's customers by name or email.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "Max results, default 10, max 50"},
            },
        },
        risk=ToolRisk.READ,
        executor=_search_customers,
        required_permission=Permission.CUSTOMER_MANAGE,
    )
    registry.register(
        name="get_customer_tickets",
        description="List all tickets belonging to a customer.",
        parameters={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_customer_tickets,
        required_permission=Permission.CUSTOMER_MANAGE,
    )
    registry.register(
        name="get_customer_history",
        description="Get a condensed history for a customer: recent tickets and staff notes.",
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "limit": {"type": "integer", "description": "Max items per section, default 10, max 50"},
            },
            "required": ["customer_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_customer_history,
        required_permission=Permission.CUSTOMER_MANAGE,
    )
    registry.register(
        name="add_customer_note",
        description="Add an internal staff note to a customer's profile. Never visible to the customer.",
        parameters={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}, "body": {"type": "string"}},
            "required": ["customer_id", "body"],
        },
        risk=ToolRisk.WRITE,
        executor=_add_customer_note,
        required_permission=Permission.CUSTOMER_MANAGE,
    )