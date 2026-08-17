from datetime import datetime
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str = Field(min_length=8)


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    role: RoleResponse
    theme: str
    notify_email: bool
    notify_alerts: bool
    notify_reports: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    theme: str | None = None
    notify_email: bool | None = None
    notify_alerts: bool | None = None
    notify_reports: bool | None = None


class UserAdminUpdate(BaseModel):
    full_name: str | None = None
    role_id: int | None = None
    is_active: bool | None = None
