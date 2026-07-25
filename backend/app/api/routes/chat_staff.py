import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.chat import ChatWidgetSettings, ChatConversation, ChatMessage, ChatConversationStatus
from app.models.ticket import Ticket, TicketComment, TicketSource, TicketStatus
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.api.deps import get_current_user
from app.core.events import emit_event, EventType
from app.schemas.chat import ChatConversationOut, ChatConversationDetailOut, ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/widget-settings", response_model=dict)
def get_or_create_widget_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    widget = db.execute(
        select(ChatWidgetSettings).where(ChatWidgetSettings.organization_id == current_user.organization_id)
    ).scalar_one_or_none()
    if not widget:
        widget = ChatWidgetSettings(organization_id=current_user.organization_id)
        db.add(widget)
        db.commit()
        db.refresh(widget)
    return {
        "public_key": widget.public_key,
        "is_active": widget.is_active,
        "welcome_message": widget.welcome_message,
    }


@router.get("/conversations", response_model=list[ChatConversationOut])
def list_conversations(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChatConversation).where(ChatConversation.organization_id == current_user.organization_id)
    if status:
        stmt = stmt.where(ChatConversation.status == status)
    stmt = stmt.order_by(ChatConversation.updated_at.desc())
    return db.execute(stmt).scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ChatConversationDetailOut)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.execute(
        select(ChatConversation).options(joinedload(ChatConversation.messages)).where(ChatConversation.id == conversation_id)
    ).unique().scalar_one_or_none()
    if not conversation or conversation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut, status_code=201)
def agent_reply(
    conversation_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or conversation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = ChatMessage(
        conversation_id=conversation.id, sender_type="agent", sender_user_id=current_user.id, body=payload.body,
    )
    db.add(message)
    conversation.updated_at = message.created_at
    if not conversation.assigned_to:
        conversation.assigned_to = current_user.id
    db.commit()
    db.refresh(message)
    return message


@router.post("/conversations/{conversation_id}/convert-to-ticket", status_code=201)
def convert_to_ticket(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_CREATE)),
):
    """Reuses Ticket/TicketComment directly — same construction pattern as
    email and n8n ingestion — rather than calling tickets.py's route
    function, which expects a different request shape. All chat messages
    become TicketComments in order, preserving the full conversation."""
    conversation = db.execute(
        select(ChatConversation).options(joinedload(ChatConversation.messages), joinedload(ChatConversation.visitor))
        .where(ChatConversation.id == conversation_id)
    ).unique().scalar_one_or_none()
    if not conversation or conversation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.ticket_id:
        raise HTTPException(status_code=400, detail="Conversation already converted to a ticket")

    visitor = conversation.visitor
    first_message = conversation.messages[0].body if conversation.messages else "(no message)"

    ticket = Ticket(
        organization_id=current_user.organization_id,
        subject=f"Chat with {visitor.name or 'website visitor'}",
        description=first_message,
        requester_name=visitor.name or "Website visitor",
        requester_email=visitor.email or "unknown@chat.local",
        created_by=current_user.id,
        source=TicketSource.WEB,
    )
    db.add(ticket)
    db.flush()

    for msg in conversation.messages:
        db.add(TicketComment(
            ticket_id=ticket.id,
            author_id=current_user.id if msg.sender_type == "agent" else current_user.id,
            body=f"[{msg.sender_type}] {msg.body}",
            is_internal_note=False,
        ))

    conversation.ticket_id = ticket.id
    conversation.status = ChatConversationStatus.CONVERTED
    db.commit()
    db.refresh(ticket)

    emit_event(
        db, EventType.TICKET_CREATED, ticket.organization_id,
        ticket=ticket,
        data={"ticket_id": str(ticket.id), "source": "chat_conversion", "conversation_id": str(conversation.id)},
    )

    return {"ticket_id": str(ticket.id)}