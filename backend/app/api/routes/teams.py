import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.team import Team, TeamMembership
from app.schemas.team import TeamCreate, TeamUpdate, TeamOut, TeamDetailOut, TeamMemberAdd
from app.api.deps import get_current_user
from app.core.permissions import require_permission, Permission

router = APIRouter(prefix="/teams", tags=["teams"])


def _with_count(db: Session, team: Team) -> Team:
    team.member_count = db.execute(
        select(func.count()).select_from(TeamMembership).where(TeamMembership.team_id == team.id)
    ).scalar_one()
    return team


@router.get("/", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teams = db.execute(
        select(Team).where(Team.organization_id == current_user.organization_id).order_by(Team.created_at.asc())
    ).scalars().all()
    return [_with_count(db, t) for t in teams]


@router.post("/", response_model=TeamOut, status_code=201)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_MANAGE)),
):
    team = Team(organization_id=current_user.organization_id, name=payload.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    team.member_count = 0
    return team


@router.get("/{team_id}", response_model=TeamDetailOut)
def get_team(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.get(Team, team_id)
    if not team or team.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Team not found")
    memberships = db.execute(select(TeamMembership).where(TeamMembership.team_id == team_id)).scalars().all()
    team.members = [m for m in (db.get(User, mem.user_id) for mem in memberships) if m]
    return team


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: uuid.UUID,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_MANAGE)),
):
    team = db.get(Team, team_id)
    if not team or team.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Team not found")
    team.name = payload.name
    db.commit()
    db.refresh(team)
    return _with_count(db, team)


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_MANAGE)),
):
    team = db.get(Team, team_id)
    if not team or team.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team)
    db.commit()


@router.post("/{team_id}/members", status_code=201)
def add_team_member(
    team_id: uuid.UUID,
    payload: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_MANAGE)),
):
    team = db.get(Team, team_id)
    if not team or team.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Team not found")
    member = db.get(User, payload.user_id)
    if not member or member.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found in this organization")

    existing = db.execute(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == payload.user_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User is already on this team")

    db.add(TeamMembership(team_id=team_id, user_id=payload.user_id))
    db.commit()


@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_MANAGE)),
):
    team = db.get(Team, team_id)
    if not team or team.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Team not found")
    membership = db.execute(
        select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == user_id)
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    db.delete(membership)
    db.commit()