"""'Conversation' here means a ticket's comment thread - Nexora has no
separate staff<->customer messaging object distinct from
Ticket/TicketComment (ChatConversation is the anonymous visitor<->staff
live-chat model, a different concern). Reusing Ticket/TicketComment
avoids inventing a parallel conversation concept."""

import uuid

from sqlalchemy import or_, select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.security.validators import MAX_LONG_FIELD_LENGTH, check_text_length
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.ai.service import AIService, AIServiceError
from app.core.permissions import Permission
from app.models.ticket import Ticket, TicketComment


def _parse_uuid(raw) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


def _get_org_ticket(ctx: AgentToolContext, ticket_id) -> Ticket | None:
    tid = _parse_uuid(ticket_id)
    if not tid:
        return None
    ticket = ctx.db.get(Ticket, tid)
    if not ticket or ticket.organization_id != ctx.organization_id:
        return None
    return ticket


async def _get_conversation(args: dict, ctx: AgentToolContext) -> ToolResult:
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    comments = ctx.db.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket.id, TicketComment.is_internal_note.is_(False))
        .order_by(TicketComment.created_at.asc())
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"Conversation has {len(comments)} public message(s).",
        data={
            "ticket_id": str(ticket.id),
            "subject": ticket.subject,
            "messages": [
                {"id": str(c.id), "author_id": str(c.author_id), "body": c.body, "created_at": c.created_at.isoformat()}
                for c in comments
            ],
        },
    )


async def _search_conversations(args: dict, ctx: AgentToolContext) -> ToolResult:
    query = (args.get("query") or "").strip()
    if not query:
        return ToolResult(success=False, summary="query is required.")

    pattern = f"%{query}%"
    matching_ticket_ids = set(
        ctx.db.execute(
            select(TicketComment.ticket_id)
            .join(Ticket, Ticket.id == TicketComment.ticket_id)
            .where(
                Ticket.organization_id == ctx.organization_id,
                TicketComment.is_internal_note.is_(False),
                TicketComment.body.ilike(pattern),
            )
        ).scalars().all()
    )

    subject_matches = ctx.db.execute(
        select(Ticket.id).where(Ticket.organization_id == ctx.organization_id, Ticket.subject.ilike(pattern))
    ).scalars().all()
    matching_ticket_ids.update(subject_matches)

    if not matching_ticket_ids:
        return ToolResult(success=True, summary="No matching conversations.", data={"tickets": []})

    limit = min(int(args.get("limit") or 10), 50)
    tickets = ctx.db.execute(
        select(Ticket).where(Ticket.id.in_(matching_ticket_ids)).order_by(Ticket.updated_at.desc()).limit(limit)
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"Found {len(tickets)} matching conversation(s).",
        data={
            "tickets": [
                {"id": str(t.id), "subject": t.subject, "status": t.status.value, "updated_at": t.updated_at.isoformat()}
                for t in tickets
            ]
        },
    )


async def _draft_customer_reply(args: dict, ctx: AgentToolContext) -> ToolResult:
    """Read-only: generates draft text via the existing AIService, same
    helper the ticket UI's 'suggest reply' button already uses. Does not
    post or send anything - use send_customer_reply (high risk, gated)
    for that."""
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    instructions = args.get("instructions")
    try:
        draft = await AIService().suggest_reply(ticket, instructions)
    except AIServiceError as exc:
        return ToolResult(success=False, summary=f"Could not generate a draft reply: {exc}")

    return ToolResult(success=True, summary="Drafted a reply (not sent).", data={"ticket_id": str(ticket.id), "draft": draft})


async def _send_customer_reply(args: dict, ctx: AgentToolContext) -> ToolResult:
    """HIGH RISK per the product spec ('send customer message'). No
    human-approval path exists until Milestone 5, so this refuses to run
    rather than posting a public comment / sending email. Still
    validates the ticket so the refusal message is meaningful."""
    ticket = _get_org_ticket(ctx, args.get("ticket_id"))
    if not ticket:
        return ToolResult(success=False, summary="Ticket not found in this organization.")

    body = (args.get("body") or "").strip()
    if not body:
        return ToolResult(success=False, summary="body is required.")
    err = check_text_length(body, "body", MAX_LONG_FIELD_LENGTH)
    if err:
        return ToolResult(success=False, summary=err)

    return ToolResult(
        success=False,
        summary=(
            "Sending a reply to the customer is a high-risk action that requires human approval, "
            "which isn't implemented until Milestone 5. No message was sent. "
            "Use draft_customer_reply to prepare the text for a human to review instead."
        ),
    )


def register(registry: AgentToolRegistry) -> None:
    # get_conversation/search_conversations: no required_permission -
    # ticket comments are returned as part of GET /tickets/{id}, which
    # has no permission gate beyond being authenticated staff.
    registry.register(
        name="get_conversation",
        description="Get the public message thread for a ticket (excludes internal notes).",
        parameters={
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}},
            "required": ["ticket_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_conversation,
    )
    registry.register(
        name="search_conversations",
        description="Search ticket subjects and public messages for text.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "Max results, default 10, max 50"},
            },
            "required": ["query"],
        },
        risk=ToolRisk.READ,
        executor=_search_conversations,
    )
    registry.register(
        name="draft_customer_reply",
        description="Generate a draft reply to the customer on a ticket. Does not send it.",
        parameters={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "instructions": {"type": "string", "description": "Optional guidance on tone/content for the draft"},
            },
            "required": ["ticket_id"],
        },
        risk=ToolRisk.READ,
        executor=_draft_customer_reply,
        # Matches the existing suggest_reply route (POST /ai/.../suggest-reply),
        # which calls the same AIService().suggest_reply() behind this permission.
        required_permission=Permission.TICKET_AI_USE,
    )
    registry.register(
        name="send_customer_reply",
        description="Send a reply to the customer on a ticket. High risk - currently requires human approval and will not execute.",
        parameters={
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}, "body": {"type": "string"}},
            "required": ["ticket_id", "body"],
        },
        risk=ToolRisk.HIGH_RISK,
        executor=_send_customer_reply,
        # Matches the public-reply path of POST /tickets/{id}/comments.
        required_permission=Permission.TICKET_COMMENT,
    )