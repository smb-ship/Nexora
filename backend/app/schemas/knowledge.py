import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgeArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    # No min_length here deliberately: the frontend's "New Article" flow
    # creates a title-only draft and lets the author fill in the body on
    # the detail page afterward. A blank body is a valid draft state.
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    status: str = "draft"


class KnowledgeArticleUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class KnowledgeArticleOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    tags: list[str]
    status: str
    author_id: uuid.UUID
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    class Config:
        from_attributes = True


class KnowledgeArticleListItem(BaseModel):
    """Lighter shape for the list view — omits body to keep the list
    endpoint's payload small; the full body is fetched on the detail page."""
    id: uuid.UUID
    title: str
    tags: list[str]
    status: str
    view_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


class SuggestedArticleOut(BaseModel):
    id: uuid.UUID
    title: str
    tags: list[str]
    reason: str