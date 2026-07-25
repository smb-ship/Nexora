import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    role: UserRole
    token: str
    status: str
    created_at: datetime
    expires_at: datetime


class InvitationPreview(BaseModel):
    email: str
    role: UserRole
    organization_name: str
    valid: bool


class InvitationAccept(BaseModel):
    full_name: str
    password: str