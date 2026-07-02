from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    agency_name: Optional[str] = None # Optional agency auto-creation on registration

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
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
