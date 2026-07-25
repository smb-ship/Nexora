"""add email integration

Revision ID: c3d4e5f6a7b8
Revises: <PASTE_YOUR_CURRENT_HEAD_REVISION_ID_HERE>
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    email_provider_type = postgresql.ENUM(
        "development",
        "smtp",
        "imap",
        "gmail",
        "microsoft365",
        "sendgrid",
        "amazon_ses",
        "mailgun",
        name="email_provider_type",
        create_type=False,
    )
    email_provider_type.create(
        op.get_bind(),
        checkfirst=True,
    )

    ticket_source = postgresql.ENUM(
        "web",
        "customer_portal",
        "email",
        name="ticket_source",
        create_type=False,
    )
    ticket_source.create(
        op.get_bind(),
        checkfirst=True,
    )

    email_status = postgresql.ENUM(
        "received",
        "pending",
        "sent",
        "failed",
        name="email_status",
        create_type=False,
    )
    email_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "email_inboxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("email_address", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("provider_type", email_provider_type, nullable=False, server_default="development"),
        sa.Column("provider_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column("tickets", sa.Column("source", ticket_source, nullable=False, server_default="web"))
    op.add_column("tickets", sa.Column("inbox_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("email_inboxes.id"), nullable=True))
    op.add_column("tickets", sa.Column("email_thread_id", sa.String(998), nullable=True))
    op.create_index("ix_tickets_email_thread_id", "tickets", ["email_thread_id"])

    op.add_column("ticket_comments", sa.Column("is_email", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("ticket_comments", sa.Column("html_body", sa.Text(), nullable=True))
    op.add_column("ticket_comments", sa.Column("email_message_id", sa.String(998), nullable=True))
    op.create_unique_constraint("uq_ticket_comments_email_message_id", "ticket_comments", ["email_message_id"])
    op.add_column("ticket_comments", sa.Column("email_in_reply_to", sa.String(998), nullable=True))
    op.add_column("ticket_comments", sa.Column("email_references", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
    op.add_column("ticket_comments", sa.Column("email_from", sa.String(255), nullable=True))
    op.add_column("ticket_comments", sa.Column("email_to", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
    op.add_column("ticket_comments", sa.Column("email_cc", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
    op.add_column("ticket_comments", sa.Column("email_bcc", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
    op.add_column("ticket_comments", sa.Column("email_status", email_status, nullable=True))

    op.create_table(
        "email_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_comments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("email_attachments")
    op.drop_column("ticket_comments", "email_status")
    op.drop_column("ticket_comments", "email_bcc")
    op.drop_column("ticket_comments", "email_cc")
    op.drop_column("ticket_comments", "email_to")
    op.drop_column("ticket_comments", "email_references")
    op.drop_column("ticket_comments", "email_in_reply_to")
    op.drop_constraint("uq_ticket_comments_email_message_id", "ticket_comments", type_="unique")
    op.drop_column("ticket_comments", "email_message_id")
    op.drop_column("ticket_comments", "html_body")
    op.drop_column("ticket_comments", "is_email")
    op.drop_index("ix_tickets_email_thread_id", table_name="tickets")
    op.drop_column("tickets", "email_thread_id")
    op.drop_column("tickets", "inbox_id")
    op.drop_column("tickets", "source")
    op.drop_table("email_inboxes")

    postgresql.ENUM(name="email_status").drop(op.get_bind())
    postgresql.ENUM(name="ticket_source").drop(op.get_bind())
    postgresql.ENUM(name="email_provider_type").drop(op.get_bind())