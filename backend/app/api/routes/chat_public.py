import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chat import ChatWidgetSettings, ChatVisitor, ChatConversation, ChatMessage, ChatConversationStatus
from app.schemas.chat import ChatSessionStart, ChatSessionOut, ChatMessageCreate, ChatMessageOut

router = APIRouter(prefix="/chat/public", tags=["chat-public"])


def _get_widget(db: Session, public_key: str) -> ChatWidgetSettings:
    widget = db.execute(
        select(ChatWidgetSettings).where(ChatWidgetSettings.public_key == public_key, ChatWidgetSettings.is_active.is_(True))
    ).scalar_one_or_none()
    if not widget:
        raise HTTPException(status_code=404, detail="Chat widget not found or inactive")
    return widget


@router.post("/{public_key}/sessions", response_model=ChatSessionOut, status_code=201)
def start_session(public_key: str, payload: ChatSessionStart, db: Session = Depends(get_db)):
    widget = _get_widget(db, public_key)

    visitor = ChatVisitor(organization_id=widget.organization_id, name=payload.name, email=payload.email)
    db.add(visitor)
    db.flush()

    conversation = ChatConversation(organization_id=widget.organization_id, visitor_id=visitor.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ChatSessionOut(conversation_id=conversation.id, visitor_id=visitor.id, welcome_message=widget.welcome_message)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut, status_code=201)
def visitor_send_message(conversation_id: uuid.UUID, payload: ChatMessageCreate, db: Session = Depends(get_db)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or conversation.status == ChatConversationStatus.CLOSED:
        raise HTTPException(status_code=404, detail="Conversation not found or closed")

    message = ChatMessage(conversation_id=conversation.id, sender_type="visitor", body=payload.body)
    db.add(message)
    conversation.updated_at = message.created_at
    db.commit()
    db.refresh(message)
    return message


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageOut])
def visitor_poll_messages(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Simple polling endpoint — the embeddable widget calls this every
    few seconds. Documented as technical debt: an SSE or WebSocket upgrade
    would reduce latency and request volume, deferred to keep this
    milestone free of new real-time infrastructure."""
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation.messages