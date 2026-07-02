from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.schemas.branding import BrandingConfigResponse

class AgencyBase(BaseModel):
    name: str
    slug: str
    settings: Dict[str, Any] = {}

class AgencyCreate(AgencyBase):
    pass

class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class AgencyResponse(AgencyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    branding_config: Optional[BrandingConfigResponse] = None
    
    # Billing & Subscriptions
    razorpay_customer_id: Optional[str] = None
    subscription_plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AgencyGoogleCredentialsUpdate(BaseModel):
    client_id: str
    client_secret: Optional[str] = None

class AgencyGoogleCredentialsResponse(BaseModel):
    client_id: Optional[str] = None
    has_secret: bool = False


class ClientBase(BaseModel):
    name: str
    industry: Optional[str] = None
    settings: Dict[str, Any] = {}

class ClientCreate(ClientBase):
    agency_id: UUID

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ClientResponse(ClientBase):
    id: UUID
    agency_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    google_place_id: Optional[str] = None
    timezone: str = "UTC"

class LocationCreate(LocationBase):
    client_id: UUID

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    google_place_id: Optional[str] = None
    timezone: Optional[str] = None

class LocationResponse(LocationBase):
    id: UUID
    client_id: UUID
    google_location_id: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
