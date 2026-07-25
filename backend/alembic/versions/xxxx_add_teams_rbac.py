"""add organizations, teams, invitations, rbac fields

Revision ID: add_teams_rbac_001
Revises: 65c8b478d092
Create Date: 2026-07-17
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_teams_rbac_001"
down_revision = "65c8b478d092"
branch_labels = None
depends_on = None


def upgrade():
    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    default_org_id = str(uuid.uuid4())
    op.execute(
        f"INSERT INTO organizations (id, name, slug, created_at) VALUES "
        f"('{default_org_id}', 'Nexora', 'nexora', now())"
    )

    # 2. user_role enum + columns on users
    # create_type=False on the reusable object: we create the Postgres type ONCE
    # explicitly below, then reuse this same object as the column type wherever
    # "user_role" is needed (users.role, invitations.role) so SQLAlchemy doesn't
    # try to CREATE TYPE a second time and error with "type already exists".
    user_role_enum = postgresql.ENUM(
        "owner",
        "admin",
        "manager",
        "agent",
        "viewer",
        name="user_role",
        create_type=False,
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=True),
    )

    op.execute(f"UPDATE users SET organization_id = '{default_org_id}'")
    # First-created account becomes owner; everyone else becomes admin (reasonable
    # default for a single-org app that's had no roles until now — reassign manually after).
    op.execute("UPDATE users SET role = 'owner' WHERE id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)")
    op.execute("UPDATE users SET role = 'admin' WHERE role IS NULL")

    op.alter_column("users", "organization_id", nullable=False)
    op.alter_column("users", "role", nullable=False)
    op.create_foreign_key("fk_users_organization", "users", "organizations", ["organization_id"], ["id"])

    # 3. tickets.organization_id
    op.add_column("tickets", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(f"UPDATE tickets SET organization_id = '{default_org_id}'")
    op.alter_column("tickets", "organization_id", nullable=False)
    op.create_foreign_key("fk_tickets_organization", "tickets", "organizations", ["organization_id"], ["id"])

    # 4. teams + team_memberships
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "team_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_membership_team_user"),
    )

    # 5. tickets.team_id (optional team assignment)
    op.add_column(
        "tickets", sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True)
    )

    # 6. invitations
    # Same reuse pattern as user_role_enum above — create the type once here,
    # then reference this SAME object (not a fresh sa.Enum(...)) in the
    # create_table call below. Using a fresh sa.Enum with the same name there
    # was the bug: it defaults to create_type=True and Postgres would reject
    # the duplicate CREATE TYPE.
    invitation_status_enum = postgresql.ENUM(
        "pending",
        "accepted",
        "revoked",
        "expired",
        name="invitation_status",
        create_type=False,
    )
    invitation_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            invitation_status_enum,  # FIXED — was a fresh sa.Enum(...) causing a duplicate CREATE TYPE
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("invitations")
    postgresql.ENUM(name="invitation_status").drop(op.get_bind(), checkfirst=True)

    op.drop_column("tickets", "team_id")
    op.drop_table("team_memberships")
    op.drop_table("teams")

    op.drop_constraint("fk_tickets_organization", "tickets", type_="foreignkey")
    op.drop_column("tickets", "organization_id")

    op.drop_constraint("fk_users_organization", "users", type_="foreignkey")
    op.drop_column("users", "role")
    op.drop_column("users", "organization_id")
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)

    op.drop_table("organizations")