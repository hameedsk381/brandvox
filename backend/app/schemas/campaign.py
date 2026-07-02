from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    target_url: Optional[str] = None
    redirect_url: Optional[str] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    target_url: Optional[str] = None
    redirect_url: Optional[str] = None
    is_active: Optional[bool] = None

class CampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: str
    target_url: Optional[str] = None
    redirect_url: Optional[str] = None
    is_active: bool
    total_sent: int
    total_opened: int
    total_converted: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class CampaignContactCreate(BaseModel):
    recipient: str
    channel: str
    employee_name: Optional[str] = None

class CampaignContactResponse(BaseModel):
    id: str
    campaign_id: str
    recipient: Optional[str] = None
    channel: Optional[str] = None
    status: str
    employee_name: Optional[str] = None
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    created_at: datetime

class CampaignAnalytics(BaseModel):
    campaign: CampaignResponse
    total_contacts: int
    sent_count: int
    opened_count: int
    converted_count: int
    open_rate: float
    conversion_rate: float

class CampaignSendRequest(BaseModel):
    contacts: List[CampaignContactCreate]

class LeaderboardEntry(BaseModel):
    employee_name: str
    requests_sent: int
    conversions: int
    conversion_rate: float

class GenerationDashboard(BaseModel):
    total_campaigns: int
    total_sent: int
    total_converted: int
    active_campaigns: int
    conversion_rate: float
    recent_campaigns: list

class FunnelFeedback(BaseModel):
    contact_id: str
    feedback_text: str
    rating: Optional[int] = None
