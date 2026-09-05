"""Ticket tools. Every executor filters on `context.organization_id` and
never trusts a model-supplied id for ownership, mirroring
app/api/routes/tickets.py's `_check_org` pattern.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.security.validators import MAX_LONG_FIELD_LENGTH, MAX_SHORT_FIELD_LENGTH, check_text_length
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.core.events import EventType, emit_event
from app.core.permissions import Permission
from app.models.ticket import Ticket, TicketComment, TicketPriority, TicketStatus
from app.models.user import User

# Statuses `change_ticket_status` is allowed to set right now. CLOSED is
# deliberately excluded - the product spec classifies closing a ticket as
# HIGH RISK, and there's no human-approval path to gate it until
# Milestone 5. Closing goes through a separate, blocked-for-now path
# below rather than silently executing.
_ALLOWED_STATUS_TRANSITIONS = {
    TicketStatus.OPEN,
    TicketStatus.PENDING,
    TicketStatus.ON_HOLD,
    TicketStatus.RESOLVED,
}


def _parse_uuid(raw, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        raise ValueError(f"'{field_name}' must be a valid UUID, got {raw!r}")


def _get_org_ticket(ctx: AgentToolContext, ticket_id: str) -> Ticket | None:
    try:
        tid = _parse_uuid(ticket_id, "ticket_id")
    except ValueError:
        return None
    ticket = ctx.db.get(Ticket, tid)
    if not ticket or ticket.organization_id != ctx.organization_id:
        return None
    return ticket


def _ticket_summary(t: Ticket) -> dict:
    return {
        "id": str(t.id),
        "subject": t.subject,
        "status": t.status.value,
        "priority": t.priority.value,
        "category": t.category.value,
        "requester_name": t.requester_name,
        "requester_email": t.requester_email,
        "assigned_to": str(t.assigned_to) if t.assigned_to else None,
        "team_id": str(t.team_id) if t.team_id else None,
        "customer_id": str(t.customer_id) if t.customer_id else None,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


async def _get_ticket(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")
    return ToolResult(success=True, summary=f"Found ticket '{ticket.subject}'.", data=_ticket_summary(ticket))


async def _search_tickets(args: dict, ctx: AgentToolContext) -> ToolResult:
    stmt = select(Ticket).where(Ticket.organization_id == ctx.organization_id)

    query = (args.get("query") or "").strip()
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Ticket.subject.ilike(pattern),
                Ticket.requester_name.ilike(pattern),
                Ticket.requester_email.ilike(pattern),
            )
        )

    status = args.get("status")
    if status:
        try:
            stmt = stmt.where(Ticket.status == TicketStatus(status))
        except ValueError:
            return ToolResult(success=False, summary=f"'{status}' is not a valid ticket status.")

    priority = args.get("priority")
    if priority:
        try:
            stmt = stmt.where(Ticket.priority == TicketPriority(priority))
        except ValueError:
            return ToolResult(success=False, summary=f"'{priority}' is not a valid ticket priority.")

    if args.get("assigned_to_me"):
        stmt = stmt.where(Ticket.assigned_to == ctx.user.id)

    limit = min(int(args.get("limit") or 10), 50)
    stmt = stmt.order_by(Ticket.updated_at.desc()).limit(limit)

    tickets = ctx.db.execute(stmt).scalars().all()
    return ToolResult(
        success=True,
        summary=f"Found {len(tickets)} ticket(s).",
        data={"tickets": [_ticket_summary(t) for t in tickets]},
    )


async def _create_ticket(args: dict, ctx: AgentToolContext) -> ToolResult:
    subject = (args.get("subject") or "").strip()
    description = (args.get("description") or "").strip()
    requester_name = (args.get("requester_name") or "").strip()
    requester_email = (args.get("requester_email") or "").strip()
    if not subject or not description or not requester_name or not requester_email:
        return ToolResult(
            success=False,
            summary="subject, description, requester_name, and requester_email are all required.",
        )
    for err in (
        check_text_length(subject, "subject", MAX_SHORT_FIELD_LENGTH),
        check_text_length(description, "description", MAX_LONG_FIELD_LENGTH),
    ):
        if err:
            return ToolResult(success=False, summary=err)

    priority = TicketPriority.MEDIUM
    if args.get("priority"):
        try:
            priority = TicketPriority(args["priority"])
        except ValueError:
            return ToolResult(success=False, summary=f"'{args['priority']}' is not a valid ticket priority.")

    team_id = None
    if args.get("team_id"):
        team_id = _parse_uuid(args["team_id"], "team_id")

    ticket = Ticket(
        organization_id=ctx.organization_id,
        subject=subject,
        description=description,
        priority=priority,
        requester_name=requester_name,
        requester_email=requester_email,
        created_by=ctx.user.id,
        team_id=team_id,
    )
    ctx.db.add(ticket)
    ctx.db.commit()
    ctx.db.refresh(ticket)

    emit_event(
        ctx.db, EventType.TICKET_CREATED, ticket.organization_id,
        ticket=ticket,
        data={
            "ticket_id": str(ticket.id), "subject": ticket.subject,
            "status": ticket.status.value, "priority": ticket.priority.value,
            "requester_email": ticket.requester_email,
        },
    )

    return ToolResult(success=True, summary=f"Created ticket '{ticket.subject}'.", data=_ticket_summary(ticket))


async def _update_ticket(args: dict, ctx: AgentToolContext) -> ToolResult:
    """Deliberately narrow: only subject/description. Status, priority,
    and assignment each have their own dedicated tool below so risk
    classification stays per-field rather than bundled into one
    catch-all writer."""
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    changed = []
    if "subject" in args and args["subject"]:
        err = check_text_length(args["subject"], "subject", MAX_SHORT_FIELD_LENGTH)
        if err:
            return ToolResult(success=False, summary=err)
        ticket.subject = args["subject"]
        changed.append("subject")
    if "description" in args and args["description"]:
        err = check_text_length(args["description"], "description", MAX_LONG_FIELD_LENGTH)
        if err:
            return ToolResult(success=False, summary=err)
        ticket.description = args["description"]
        changed.append("description")

    if not changed:
        return ToolResult(success=False, summary="Nothing to update - provide subject and/or description.")

    ctx.db.commit()
    ctx.db.refresh(ticket)
    return ToolResult(
        success=True, summary=f"Updated {', '.join(changed)} on ticket '{ticket.subject}'.",
        data=_ticket_summary(ticket),
    )


async def _change_ticket_status(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    raw_status = args.get("status")
    try:
        new_status = TicketStatus(raw_status)
    except (ValueError, TypeError):
        return ToolResult(success=False, summary=f"'{raw_status}' is not a valid ticket status.")

    if new_status not in _ALLOWED_STATUS_TRANSITIONS:
        return ToolResult(
            success=False,
            summary=(
                "Closing a ticket is a high-risk action that requires human approval, "
                "which isn't implemented until Milestone 5. This tool currently supports "
                "open, pending, on_hold, and resolved only."
            ),
        )

    old_status = ticket.status
    ticket.status = new_status
    ctx.db.commit()
    ctx.db.refresh(ticket)

    if new_status != old_status:
        emit_event(
            ctx.db, EventType.TICKET_STATUS_CHANGED, ticket.organization_id, ticket=ticket,
            data={"ticket_id": str(ticket.id), "old_status": old_status.value, "new_status": new_status.value},
        )

    return ToolResult(
        success=True, summary=f"Changed status from {old_status.value} to {new_status.value}.",
        data=_ticket_summary(ticket),
    )


async def _change_ticket_priority(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    raw_priority = args.get("priority")
    try:
        new_priority = TicketPriority(raw_priority)
    except (ValueError, TypeError):
        return ToolResult(success=False, summary=f"'{raw_priority}' is not a valid ticket priority.")

    old_priority = ticket.priority
    ticket.priority = new_priority
    ctx.db.commit()
    ctx.db.refresh(ticket)

    if new_priority != old_priority:
        emit_event(
            ctx.db, EventType.TICKET_PRIORITY_CHANGED, ticket.organization_id, ticket=ticket,
            data={"ticket_id": str(ticket.id), "old_priority": old_priority.value, "new_priority": new_priority.value},
        )

    return ToolResult(
        success=True, summary=f"Changed priority from {old_priority.value} to {new_priority.value}.",
        data=_ticket_summary(ticket),
    )


async def _assign_ticket(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    raw_assignee = args.get("assigned_to")
    new_assignee = None
    if raw_assignee:
        new_assignee = _parse_uuid(raw_assignee, "assigned_to")
        assignee = ctx.db.get(User, new_assignee)
        if not assignee or assignee.organization_id != ctx.organization_id:
            return ToolResult(success=False, summary="assigned_to must be a staff user in this organization.")

    old_assignee = ticket.assigned_to
    ticket.assigned_to = new_assignee
    ctx.db.commit()
    ctx.db.refresh(ticket)

    if new_assignee != old_assignee:
        event_type = EventType.TICKET_ASSIGNED if new_assignee else EventType.TICKET_UNASSIGNED
        emit_event(
            ctx.db, event_type, ticket.organization_id, ticket=ticket,
            data={"ticket_id": str(ticket.id), "assigned_to": str(new_assignee) if new_assignee else None},
        )

    label = "unassigned" if not new_assignee else f"assigned to {new_assignee}"
    return ToolResult(success=True, summary=f"Ticket '{ticket.subject}' {label}.", data=_ticket_summary(ticket))


async def _add_internal_note(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    body = (args.get("body") or "").strip()
    if not body:
        return ToolResult(success=False, summary="body is required.")
    err = check_text_length(body, "body", MAX_LONG_FIELD_LENGTH)
    if err:
        return ToolResult(success=False, summary=err)

    comment = TicketComment(ticket_id=ticket.id, author_id=ctx.user.id, body=body, is_internal_note=True)
    ctx.db.add(comment)
    ticket.updated_at = datetime.now(timezone.utc)
    ctx.db.commit()
    ctx.db.refresh(comment)

    return ToolResult(
        success=True, summary="Added an internal note (not visible to the customer).",
        data={"comment_id": str(comment.id), "ticket_id": str(ticket.id), "created_at": comment.created_at.isoformat()},
    )


async def _get_ticket_history(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    comments = ctx.db.execute(
        select(TicketComment).where(TicketComment.ticket_id == ticket.id).order_by(TicketComment.created_at.asc())
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"Ticket has {len(comments)} comment(s).",
        data={
            "ticket": _ticket_summary(ticket),
            "comments": [
                {
                    "id": str(c.id),
                    "author_id": str(c.author_id),
                    "body": c.body,
                    "is_internal_note": c.is_internal_note,
                    "is_email": c.is_email,
                    "created_at": c.created_at.isoformat(),
                }
                for c in comments
            ],
        },
    )


def register(registry: AgentToolRegistry) -> None:
    registry.register(
        name="get_ticket",
        description="Get full details of a single ticket by its id.",
        parameters={
            "type": "object",
            "properties": {"ticket_id": {"type": "string", "description": "UUID of the ticket"}},
            "required": ["ticket_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_ticket,
    )
    registry.register(
        name="search_tickets",
        description="Search this organization's tickets by subject/requester text, status, and/or priority.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Free-text search across subject/requester name/email"},
                "status": {"type": "string", "enum": [s.value for s in TicketStatus]},
                "priority": {"type": "string", "enum": [p.value for p in TicketPriority]},
                "assigned_to_me": {"type": "boolean", "description": "Only tickets assigned to the calling staff user"},
                "limit": {"type": "integer", "description": "Max results, default 10, max 50"},
            },
        },
        risk=ToolRisk.READ,
        executor=_search_tickets,
    )
    registry.register(
        name="create_ticket",
        description="Create a new support ticket.",
        parameters={
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "requester_name": {"type": "string"},
                "requester_email": {"type": "string"},
                "priority": {"type": "string", "enum": [p.value for p in TicketPriority]},
                "team_id": {"type": "string", "description": "UUID of a team to route this to, optional"},
            },
            "required": ["subject", "description", "requester_name", "requester_email"],
        },
        risk=ToolRisk.WRITE,
        executor=_create_ticket,
        required_permission=Permission.TICKET_CREATE,
    )
    registry.register(
        name="update_ticket",
        description="Update a ticket's subject and/or description (not status/priority/assignment - use the dedicated tools for those).",
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "subject": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["ticket_id"],
        },
        risk=ToolRisk.WRITE,
        executor=_update_ticket,
        # Matches the existing PATCH /tickets/{id} route, which gates
        # this same subject/description/status/priority/assignment
        # bundle behind a single permission.
        required_permission=Permission.TICKET_UPDATE_STATUS,
    )
    registry.register(
        name="change_ticket_status",
        description=(
            "Change a ticket's status to open, pending, on_hold, or resolved. "
            "Closing a ticket is not supported by this tool - it requires human approval."
        ),
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "status": {"type": "string", "enum": [s.value for s in TicketStatus]},
            },
            "required": ["ticket_id", "status"],
        },
        risk=ToolRisk.WRITE,
        executor=_change_ticket_status,
        required_permission=Permission.TICKET_UPDATE_STATUS,
    )
    registry.register(
        name="change_ticket_priority",
        description="Change a ticket's priority.",
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "priority": {"type": "string", "enum": [p.value for p in TicketPriority]},
            },
            "required": ["ticket_id", "priority"],
        },
        risk=ToolRisk.WRITE,
        executor=_change_ticket_priority,
        required_permission=Permission.TICKET_UPDATE_PRIORITY,
    )
    registry.register(
        name="assign_ticket",
        description="Assign a ticket to a staff user, or unassign it by omitting assigned_to.",
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "assigned_to": {"type": "string", "description": "UUID of the staff user to assign to; omit to unassign"},
            },
            "required": ["ticket_id"],
        },
        risk=ToolRisk.WRITE,
        executor=_assign_ticket,
        required_permission=Permission.TICKET_ASSIGN,
    )
    registry.register(
        name="add_internal_note",
        description="Add an internal note to a ticket. Never visible to the customer.",
        parameters={
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}, "body": {"type": "string"}},
            "required": ["ticket_id", "body"],
        },
        risk=ToolRisk.WRITE,
        executor=_add_internal_note,
        required_permission=Permission.TICKET_INTERNAL_NOTE,
    )
    registry.register(
        name="get_ticket_history",
        description="Get a ticket's full comment history (public replies and internal notes) in chronological order.",
        parameters={
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}},
            "required": ["ticket_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_ticket_history,
    )