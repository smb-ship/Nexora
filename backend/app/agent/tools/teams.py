import uuid

from sqlalchemy import select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.models.team import Team, TeamMembership
from app.models.user import User


def _parse_uuid(raw) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


async def _list_teams(args: dict, ctx: AgentToolContext) -> ToolResult:
    teams = ctx.db.execute(
        select(Team).where(Team.organization_id == ctx.organization_id).order_by(Team.created_at.asc())
    ).scalars().all()

    return ToolResult(
        success=True,
        summary=f"Found {len(teams)} team(s).",
        data={"teams": [{"id": str(t.id), "name": t.name} for t in teams]},
    )


async def _list_team_members(args: dict, ctx: AgentToolContext) -> ToolResult:
    team_id = _parse_uuid(args.get("team_id"))
    if not team_id:
        return ToolResult(success=False, summary="team_id must be a valid UUID.")

    team = ctx.db.get(Team, team_id)
    if not team or team.organization_id != ctx.organization_id:
        return ToolResult(success=False, summary="Team not found in this organization.")

    memberships = ctx.db.execute(select(TeamMembership).where(TeamMembership.team_id == team_id)).scalars().all()
    member_ids = [m.user_id for m in memberships]
    members = ctx.db.execute(select(User).where(User.id.in_(member_ids))).scalars().all() if member_ids else []

    return ToolResult(
        success=True,
        summary=f"Team '{team.name}' has {len(members)} member(s).",
        data={
            "team": {"id": str(team.id), "name": team.name},
            "members": [{"id": str(m.id), "full_name": m.full_name, "email": m.email, "role": m.role.value} for m in members],
        },
    )


def register(registry: AgentToolRegistry) -> None:
    registry.register(
        name="list_teams",
        description="List all teams in this organization.",
        parameters={"type": "object", "properties": {}},
        risk=ToolRisk.READ,
        executor=_list_teams,
    )
    registry.register(
        name="list_team_members",
        description="List the staff members of a given team.",
        parameters={
            "type": "object",
            "properties": {"team_id": {"type": "string"}},
            "required": ["team_id"],
        },
        risk=ToolRisk.READ,
        executor=_list_team_members,
    )