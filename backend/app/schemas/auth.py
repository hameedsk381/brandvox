from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.core.auth import validate_password_strength

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    agency_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        err = validate_password_strength(v)
        if err:
            raise ValueError(err)
        return v

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    mfa_enabled: bool = False
    agency_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    mfa_required: bool = False
    mfa_token: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        err = validate_password_strength(v)
        if err:
            raise ValueError(err)
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        err = validate_password_strength(v)
        if err:
            raise ValueError(err)
        return v

class MfaSetupResponse(BaseModel):
    secret: str
    uri: str
    qr_code_url: str

class MfaVerifyRequest(BaseModel):
    code: str

class MfaLoginVerifyRequest(BaseModel):
    mfa_token: str
    code: str

class ExportDataResponse(BaseModel):
    user: UserResponse
    data: dict
