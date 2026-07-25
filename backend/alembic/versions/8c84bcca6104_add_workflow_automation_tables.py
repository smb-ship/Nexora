"""add workflow automation tables

Revision ID: a1b2c3d4e5f6
Revises: <PASTE_YOUR_CURRENT_HEAD_REVISION_ID_HERE>
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "95d355c8372f"
branch_labels = None
depends_on = None


def upgrade():
    workflow_trigger_type = postgresql.ENUM(
        "ticket_created",
        "ticket_status_changed",
        "ticket_priority_changed",
        "ticket_assigned",
        "ticket_unassigned",
        "ticket_comment_added",
        "ticket_sentiment_changed",
        "ticket_idle",
        name="workflow_trigger_type",
        create_type=False,
    )
    workflow_trigger_type.create(op.get_bind(), checkfirst=True)

    workflow_condition_field = postgresql.ENUM(
        "status",
        "priority",
        "sentiment",
        "team_id",
        "assigned_to",
        "is_unassigned",
        "subject",
        "description",
        "hours_since_updated",
        "hours_since_created",
        name="workflow_condition_field",
        create_type=False,
    )
    workflow_condition_field.create(op.get_bind(), checkfirst=True)

    workflow_operator = postgresql.ENUM(
        "equals",
        "not_equals",
        "in",
        "contains",
        "greater_than",
        "less_than",
        "is_empty",
        "is_not_empty",
        name="workflow_operator",
        create_type=False,
    )
    workflow_operator.create(op.get_bind(), checkfirst=True)

    workflow_action_type = postgresql.ENUM(
        "assign_team",
        "assign_user",
        "unassign",
        "set_priority",
        "set_status",
        "add_internal_note",
        name="workflow_action_type",
        create_type=False,
    )
    workflow_action_type.create(op.get_bind(), checkfirst=True)

    workflow_condition_logic = postgresql.ENUM(
        "all",
        "any",
        name="workflow_condition_logic",
        create_type=False,
    )
    workflow_condition_logic.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "workflow_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", workflow_trigger_type, nullable=False),
        sa.Column("condition_logic", workflow_condition_logic, nullable=False, server_default="all"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("run_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "workflow_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field", workflow_condition_field, nullable=False),
        sa.Column("operator", workflow_operator, nullable=False),
        sa.Column("value", sa.String(500), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "workflow_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", workflow_action_type, nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "workflow_execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_type", workflow_trigger_type, nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("actions_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("workflow_execution_logs")
    op.drop_table("workflow_actions")
    op.drop_table("workflow_conditions")
    op.drop_table("workflow_rules")

    postgresql.ENUM(name="workflow_condition_logic").drop(op.get_bind())
    postgresql.ENUM(name="workflow_action_type").drop(op.get_bind())
    postgresql.ENUM(name="workflow_operator").drop(op.get_bind())
    postgresql.ENUM(name="workflow_condition_field").drop(op.get_bind())
    postgresql.ENUM(name="workflow_trigger_type").drop(op.get_bind())