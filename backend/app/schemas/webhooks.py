from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

EVENT_TYPES = [
    "review.created",
    "reply.posted",
    "crisis.detected",
    "sync.completed",
    "report.generated",
    "score.changed",
]

class WebhookEndpointCreate(BaseModel):
    name: str
    url: str
    event_types: List[str]
    secret: Optional[str] = None

class WebhookEndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    event_types: Optional[List[str]] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None

class WebhookEndpointResponse(BaseModel):
    id: UUID
    name: str
    url: str
    event_types: List[str]
    is_active: bool
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    failure_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookDeliveryResponse(BaseModel):
    id: UUID
    endpoint_id: UUID
    event_type: str
    response_status: Optional[int] = None
    success: bool
    attempt: int
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookTestEvent(BaseModel):
    event_type: str = "webhook.test"
