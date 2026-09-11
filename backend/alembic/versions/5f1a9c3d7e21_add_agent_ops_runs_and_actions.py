"""add_agent_ops_runs_and_actions

Revision ID: 5f1a9c3d7e21
Revises: 3b7729815cbe
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f1a9c3d7e21'
down_revision: Union[str, Sequence[str], None] = '3b7729815cbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('agent_runs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('agent_name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.Enum('running', 'completed', 'failed', name='agent_run_status'), nullable=False),
    sa.Column('initial_request', sa.Text(), nullable=False),
    sa.Column('current_step', sa.String(length=255), nullable=True),
    sa.Column('final_result', sa.Text(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('agent_actions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('run_id', sa.UUID(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('tool_name', sa.String(length=100), nullable=False),
    sa.Column('arguments', sa.JSON(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('risk', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('agent_actions')
    op.drop_table('agent_runs')
    op.execute('DROP TYPE IF EXISTS agent_run_status')