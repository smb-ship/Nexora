import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.organization import OrgMemberOut, MemberRoleUpdate
from app.api.deps import get_current_user
from app.core.permissions import require_permission, Permission

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/members", response_model=list[OrgMemberOut])
def list_members(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.execute(
        select(User).where(User.organization_id == current_user.organization_id).order_by(User.created_at.asc())
    ).scalars().all()


@router.patch("/members/{user_id}", response_model=OrgMemberOut)
def update_member_role(
    user_id: uuid.UUID,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_ROLE_MANAGE)),
):
    member = db.get(User, user_id)
    if not member or member.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == UserRole.OWNER and current_user.id != member.id:
        raise HTTPException(status_code=403, detail="Only the owner can change their own role")
    if payload.role == UserRole.OWNER:
        raise HTTPException(status_code=400, detail="Ownership transfer isn't supported yet")

    member.role = payload.role
    db.commit()
    db.refresh(member)
    return member