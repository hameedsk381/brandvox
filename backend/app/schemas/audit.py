from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class AuditLogBase(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    agency_id: UUID
    user_id: Optional[UUID] = None

class AuditLogResponse(AuditLogBase):
    id: UUID
    agency_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    
    # Optional expanded user info for frontend display
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True
