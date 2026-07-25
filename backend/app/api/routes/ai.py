import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import Ticket
from app.models.ticket_ai_insight import TicketAIInsight
from app.models.user import User
from app.api.deps import get_current_user
from app.core.permissions import require_permission, Permission
from app.core.config import settings
from app.ai.service import AIService, AIServiceError
from app.schemas.ai import AIInsightOut, ReplySuggestionRequest, ReplySuggestionOut
from app.workflows.engine import run_workflows
from app.workflows.enums import WorkflowTriggerType

router = APIRouter(prefix="/tickets/{ticket_id}/ai", tags=["ai"])


def _get_ticket(ticket_id: uuid.UUID, current_user: User, db: Session) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def _get_or_create_insight(ticket_id: uuid.UUID, db: Session) -> TicketAIInsight:
    insight = db.execute(
        select(TicketAIInsight).where(TicketAIInsight.ticket_id == ticket_id)
    ).scalar_one_or_none()
    if not insight:
        insight = TicketAIInsight(ticket_id=ticket_id)
        db.add(insight)
    return insight


@router.get("/insights", response_model=AIInsightOut | None)
def get_insights(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    _get_ticket(ticket_id, current_user, db)
    return db.execute(
        select(TicketAIInsight).where(TicketAIInsight.ticket_id == ticket_id)
    ).scalar_one_or_none()


@router.post("/summarize", response_model=AIInsightOut)
async def summarize_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        summary = await AIService().summarize(ticket)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc

    insight = _get_or_create_insight(ticket_id, db)
    insight.summary = summary
    insight.model_used = settings.GEMINI_MODEL
    insight.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/sentiment", response_model=AIInsightOut)
async def analyze_sentiment(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        sentiment, score = await AIService().analyze_sentiment(ticket)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc

    insight = _get_or_create_insight(ticket_id, db)
    insight.sentiment = sentiment
    insight.sentiment_score = score
    insight.model_used = settings.GEMINI_MODEL
    insight.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)

    run_workflows(db, WorkflowTriggerType.TICKET_SENTIMENT_CHANGED, ticket)

    return insight


@router.post("/predict-priority", response_model=AIInsightOut)
async def predict_priority(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        priority = await AIService().predict_priority(ticket)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc

    insight = _get_or_create_insight(ticket_id, db)
    insight.predicted_priority = priority
    insight.model_used = settings.GEMINI_MODEL
    insight.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/suggest-tags", response_model=AIInsightOut)
async def suggest_tags(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        tags = await AIService().suggest_tags(ticket)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc

    insight = _get_or_create_insight(ticket_id, db)
    insight.suggested_tags = tags
    insight.model_used = settings.GEMINI_MODEL
    insight.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/suggest-reply", response_model=ReplySuggestionOut)
async def suggest_reply(
    ticket_id: uuid.UUID,
    payload: ReplySuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        reply = await AIService().suggest_reply(ticket, payload.instructions)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc
    return ReplySuggestionOut(reply=reply)


@router.post("/internal-note", response_model=AIInsightOut)
async def generate_internal_note(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    ticket = _get_ticket(ticket_id, current_user, db)
    try:
        note = await AIService().generate_internal_note(ticket)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not process this request") from exc

    insight = _get_or_create_insight(ticket_id, db)
    insight.internal_ai_notes = note
    insight.model_used = settings.GEMINI_MODEL
    insight.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(insight)
    return insight