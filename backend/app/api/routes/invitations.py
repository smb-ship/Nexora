import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.invitation import Invitation, InvitationStatus
from app.models.organization import Organization
from app.schemas.invitation import InvitationCreate, InvitationOut, InvitationPreview, InvitationAccept
from app.api.v1.auth import COOKIE_KWARGS
from app.core.config import settings
from app.core.permissions import require_permission, Permission
from app.core.security import create_access_token, create_refresh_token, hash_password

router = APIRouter(prefix="/invitations", tags=["invitations"])
INVITATION_EXPIRY_DAYS = 7


@router.post("/", response_model=InvitationOut, status_code=201)
def create_invitation(
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_INVITE)),
):
    existing_member = db.execute(
        select(User).where(User.organization_id == current_user.organization_id, User.email == payload.email)
    ).scalar_one_or_none()
    if existing_member:
        raise HTTPException(status_code=400, detail="This person is already a member of your organization")

    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=payload.email,
        role=payload.role,
        token=secrets.token_urlsafe(32),
        invited_by=current_user.id,
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


@router.get("/", response_model=list[InvitationOut])
def list_invitations(db: Session = Depends(get_db), current_user: User = Depends(require_permission(Permission.TEAM_INVITE))):
    return db.execute(
        select(Invitation)
        .where(Invitation.organization_id == current_user.organization_id, Invitation.status == InvitationStatus.PENDING)
        .order_by(Invitation.created_at.desc())
    ).scalars().all()


@router.delete("/{invitation_id}", status_code=204)
def revoke_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TEAM_INVITE)),
):
    invitation = db.get(Invitation, invitation_id)
    if not invitation or invitation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    invitation.status = InvitationStatus.REVOKED
    db.commit()


# --- Public endpoints (no auth) — used by the accept-invite page ---

@router.get("/token/{token}", response_model=InvitationPreview)
def preview_invitation(token: str, db: Session = Depends(get_db)):
    invitation = db.execute(select(Invitation).where(Invitation.token == token)).scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    valid = invitation.status == InvitationStatus.PENDING and invitation.expires_at > datetime.now(timezone.utc)
    org = db.get(Organization, invitation.organization_id)
    return InvitationPreview(
        email=invitation.email, role=invitation.role, organization_name=org.name if org else "", valid=valid,
    )


@router.post("/token/{token}/accept")
def accept_invitation(token: str, payload: InvitationAccept, response: Response, db: Session = Depends(get_db)):
    invitation = db.execute(select(Invitation).where(Invitation.token == token)).scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="This invitation is no longer valid")
    if invitation.expires_at <= datetime.now(timezone.utc):
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="This invitation has expired")

    existing = db.execute(select(User).where(User.email == invitation.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        email=invitation.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        organization_id=invitation.organization_id,
        role=invitation.role,
    )
    db.add(user)
    invitation.status = InvitationStatus.ACCEPTED
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    response.set_cookie("access_token", access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **COOKIE_KWARGS)
    response.set_cookie("refresh_token", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **COOKIE_KWARGS)

    return {"id": str(user.id), "email": user.email}