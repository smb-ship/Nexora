"""add_ticket_ai_insights_table

Revision ID: 95d355c8372f
Revises: add_teams_rbac_001
Create Date: 2026-07-18 09:51:32.336578
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '95d355c8372f'
down_revision: Union[str, Sequence[str], None] = 'add_teams_rbac_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sentiment_enum = postgresql.ENUM(
        "positive", "neutral", "negative", "frustrated",
        name="ticket_sentiment",
    )
    sentiment_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = postgresql.ENUM(
        "low", "medium", "high", "urgent",
        name="ticket_priority",
        create_type=False,
    )

    op.create_table(
        "ticket_ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment", postgresql.ENUM(
            "positive", "neutral", "negative", "frustrated",
            name="ticket_sentiment",
            create_type=False,
        ), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("predicted_priority", priority_enum, nullable=True),
        sa.Column("suggested_tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("internal_ai_notes", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=100), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_ai_insights")
    postgresql.ENUM(name="ticket_sentiment").drop(op.get_bind(), checkfirst=True)