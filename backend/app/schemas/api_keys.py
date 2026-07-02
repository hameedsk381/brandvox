from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class ApiKeyCreate(BaseModel):
    name: str
    scopes: List[str] = ["read"]

class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    scopes: Optional[List[str]] = None
