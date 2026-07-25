import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.user import UserRole


class OrgMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str | None = None
    email: str
    role: UserRole
    created_at: datetime


class MemberRoleUpdate(BaseModel):
    role: UserRole