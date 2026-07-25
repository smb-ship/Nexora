import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.ticket import TicketPriority
from app.models.ticket_ai_insight import SentimentLabel


class AIInsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ticket_id: uuid.UUID
    summary: str | None
    sentiment: SentimentLabel | None
    sentiment_score: float | None
    predicted_priority: TicketPriority | None
    suggested_tags: list[str]
    internal_ai_notes: str | None
    model_used: str | None
    generated_at: datetime | None
    updated_at: datetime


class ReplySuggestionRequest(BaseModel):
    instructions: str | None = None


class ReplySuggestionOut(BaseModel):
    reply: str