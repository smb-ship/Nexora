import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.orchestrator import AgentError, AgentOrchestrator
from app.agent.tool_registry import ToolContext, build_default_registry
from app.core.customer_auth import require_customer
from app.db.session import get_db
from app.models.agent_conversation import AgentConversation, AgentMessage, AgentMessageRole
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentConversationOut, AgentMessageOut

router = APIRouter(prefix="/agent", tags=["agent"])

# Built once at import time - Milestone 4 will register real tools here.
# No per-request cost since ToolRegistry only holds definitions/callables.
_registry = build_default_registry()


def _load_history(conversation: AgentConversation) -> list[dict]:
    """Rebuilds the provider-agnostic message list from persisted rows."""
    history: list[dict] = []
    for msg in conversation.messages:
        if msg.role == AgentMessageRole.USER:
            history.append({"role": "user", "content": msg.content})
        elif msg.role == AgentMessageRole.ASSISTANT:
            history.append({"role": "assistant", "content": msg.content, "tool_calls": []})
        elif msg.role == AgentMessageRole.TOOL:
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.tool_name,
                    "content": msg.content or "",
                }
            )
    return history


def _get_owned_conversation(db: Session, conversation_id: uuid.UUID, current_user: User) -> AgentConversation:
    conversation = db.get(AgentConversation, conversation_id)
    if not conversation or conversation.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations", response_model=AgentConversationOut, status_code=201)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    conversation = AgentConversation(
        organization_id=current_user.organization_id,
        customer_id=current_user.id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}", response_model=AgentConversationOut)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    return _get_owned_conversation(db, conversation_id, current_user)


@router.post("/conversations/{conversation_id}/messages", response_model=AgentChatResponse)
async def send_message(
    conversation_id: uuid.UUID,
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    conversation = _get_owned_conversation(db, conversation_id, current_user)
    history = _load_history(conversation)

    db.add(
        AgentMessage(
            conversation_id=conversation.id,
            role=AgentMessageRole.USER,
            content=payload.message,
        )
    )
    db.commit()

    orchestrator = AgentOrchestrator(tool_registry=_registry)
    context = ToolContext(db=db, customer=current_user, organization_id=current_user.organization_id)

    try:
        result = await orchestrator.run_turn(history, payload.message, context)
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    assistant_row = AgentMessage(
        conversation_id=conversation.id,
        role=AgentMessageRole.ASSISTANT,
        content=result.content,
    )
    db.add(assistant_row)
    conversation.updated_at = assistant_row.created_at
    db.commit()
    db.refresh(assistant_row)

    return AgentChatResponse(
        message=AgentMessageOut(
            id=assistant_row.id,
            role="assistant",
            content=assistant_row.content,
            created_at=assistant_row.created_at,
        ),
        tool_trace=result.trace,
    )