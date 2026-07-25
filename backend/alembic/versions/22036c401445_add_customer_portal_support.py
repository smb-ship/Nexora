"""add customer portal support

Revision ID: b2c3d4e5f6a7
Revises: <PASTE_YOUR_CURRENT_HEAD_REVISION_ID_HERE>
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # user_role uses values_callable (lowercase values) — 'customer' matches that convention.
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'customer'")

    # ticket_category follows ticket_status/ticket_priority's convention on the
    # same table: no values_callable, so Postgres labels are the enum member NAMES.
    ticket_category = postgresql.ENUM(
        "GENERAL", "TECHNICAL", "BILLING", "FEATURE_REQUEST", "OTHER",
        name="ticket_category",
    )
    ticket_category.create(op.get_bind())

    op.add_column(
        "tickets",
        sa.Column("category", ticket_category, nullable=False, server_default="GENERAL"),
    )
    op.add_column(
        "tickets",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])


def downgrade():
    op.drop_index("ix_tickets_customer_id", table_name="tickets")
    op.drop_column("tickets", "customer_id")
    op.drop_column("tickets", "category")
    postgresql.ENUM(name="ticket_category").drop(op.get_bind())
    # Note: Postgres does not support removing a value from an existing enum
    # type, so 'customer' remains in user_role even after downgrade. This is
    # a one-way migration in that respect — acceptable for a role addition.