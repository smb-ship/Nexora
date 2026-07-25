import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Float, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.models.ticket import TicketPriority


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class TicketAIInsight(Base):
    __tablename__ = "ticket_ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), unique=True, nullable=False
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    sentiment: Mapped[SentimentLabel | None] = mapped_column(
        SAEnum(
            SentimentLabel,
            name="ticket_sentiment",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    predicted_priority: Mapped[TicketPriority | None] = mapped_column(
        SAEnum(TicketPriority, name="ticket_priority", create_type=False), nullable=True
    )

    suggested_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    internal_ai_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    ticket = relationship("Ticket", foreign_keys=[ticket_id])