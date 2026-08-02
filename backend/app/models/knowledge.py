import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class KnowledgeArticle(Base):
    """Org-scoped help article. Tags use a plain string array (same pattern
    as OutgoingWebhook.event_types) rather than a separate tags table —
    simple enough at this scale, and avoids a join for search/filtering."""

    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    status: Mapped[ArticleStatus] = mapped_column(
        SAEnum(ArticleStatus, name="article_status", values_callable=lambda e: [m.value for m in e]),
        default=ArticleStatus.DRAFT, nullable=False,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Sentence-embedding of title+body, recomputed on create/update. Null
    # until first computed (e.g. rows from before this migration). Plain
    # float array + Python cosine similarity rather than a vector-DB
    # extension — fine at this scale (see app/ai/embeddings.py).
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author = relationship("User", foreign_keys=[author_id])