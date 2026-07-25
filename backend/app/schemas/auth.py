from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    # This becomes the new Organization's name. Registration always creates
    # a brand-new organization with this user as its Owner — there is no
    # public path to join an *existing* org (that's what the invitation
    # flow is for), so this field is required, not optional.
    organization_name: str = Field(min_length=2, max_length=255)