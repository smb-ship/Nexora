import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str | None = None
    email: str


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime
    member_count: int = 0


class TeamDetailOut(TeamOut):
    members: list[TeamMemberOut] = []


class TeamMemberAdd(BaseModel):
    user_id: uuid.UUID