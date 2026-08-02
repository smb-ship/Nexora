import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)


class CitedArticle(BaseModel):
    id: uuid.UUID
    title: str
    similarity: float


class RAGQueryResponse(BaseModel):
    answer: str
    cited_articles: list[CitedArticle]


class PromptTemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    prompt_text: str = Field(min_length=1)
    category: str = "general"


class PromptTemplateOut(BaseModel):
    id: uuid.UUID
    title: str
    prompt_text: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketInsightSummaryOut(BaseModel):
    ticket_id: uuid.UUID
    ticket_subject: str
    summary: str | None
    sentiment: str | None
    predicted_priority: str | None
    suggested_tags: list[str]
    generated_at: datetime