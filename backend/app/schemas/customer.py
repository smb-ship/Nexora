import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    # Staff sets an initial password directly since there's no email/invite
    # infrastructure for customers yet (see Known Technical Debt). The
    # customer can change it after logging in once a password-change
    # endpoint exists.
    password: str = Field(min_length=8)


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime