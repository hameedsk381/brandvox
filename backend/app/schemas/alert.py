from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.alert import AlertSeverity, AlertCategory, AlertStatus, IntegrationType

class AlertIntegrationBase(BaseModel):
    type: IntegrationType
    webhook_url: HttpUrl
    is_active: bool = True

class AlertIntegrationCreate(AlertIntegrationBase):
    pass

class AlertIntegrationResponse(AlertIntegrationBase):
    id: UUID
    location_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class CrisisAlertBase(BaseModel):
    severity: AlertSeverity
    category: AlertCategory
    analysis_reason: Optional[str] = None

class CrisisAlertCreate(CrisisAlertBase):
    review_id: UUID

class CrisisAlertResponse(CrisisAlertBase):
    id: UUID
    location_id: UUID
    review_id: UUID
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Extra fields for UI convenience
    review_text: Optional[str] = None
    author_name: Optional[str] = None
    rating: Optional[int] = None

    class Config:
        from_attributes = True
