from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class BrandVoiceProfileBase(BaseModel):
    tone: str = "professional" # friendly, professional, premium, medical, hospitality, corporate, casual
    vocabulary_notes: Optional[str] = None
    greeting_style: Optional[str] = None
    closing_style: Optional[str] = None
    example_replies: List[str] = []
    personality_traits: List[str] = []

class BrandVoiceProfileCreate(BrandVoiceProfileBase):
    client_id: UUID

class BrandVoiceProfileUpdate(BaseModel):
    tone: Optional[str] = None
    vocabulary_notes: Optional[str] = None
    greeting_style: Optional[str] = None
    closing_style: Optional[str] = None
    example_replies: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None

class BrandVoiceProfileResponse(BrandVoiceProfileBase):
    id: UUID
    client_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SmartRuleBase(BaseModel):
    min_rating: int
    max_rating: int
    action: str # auto_reply, approval_required, escalate, never_auto
    notify_roles: List[str] = []
    is_active: bool = True

class SmartRuleCreate(SmartRuleBase):
    location_id: UUID

class SmartRuleUpdate(BaseModel):
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    action: Optional[str] = None
    notify_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None

class SmartRuleResponse(SmartRuleBase):
    id: UUID
    location_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
