from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class SeoProfileResponse(BaseModel):
    id: UUID
    location_id: UUID
    gbp_completeness_score: int
    gbp_missing_fields: list
    gbp_photo_count: int
    gbp_post_count: int
    gbp_response_rate: float
    last_audit_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class KeywordRankingCreate(BaseModel):
    keyword: str
    current_rank: Optional[int] = None
    search_volume: Optional[str] = None

class KeywordRankingResponse(BaseModel):
    id: UUID
    location_id: UUID
    keyword: str
    current_rank: Optional[int] = None
    previous_rank: Optional[int] = None
    search_volume: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CitationRecordResponse(BaseModel):
    id: UUID
    location_id: UUID
    directory_name: str
    url: Optional[str] = None
    nap_consistent: bool
    issues: list
    last_checked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SeoAuditResult(BaseModel):
    location_id: str
    completeness_score: int
    missing_fields: List[str]
    photo_count: int
    post_count: int
    response_rate: float
    recommendations: List[str]

class CompetitorMapsRankingResponse(BaseModel):
    id: UUID
    competitor_id: UUID
    competitor_name: Optional[str] = None
    keyword: str
    rank: Optional[int] = None
    previous_rank: Optional[int] = None
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GbpPostScheduleCreate(BaseModel):
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    media_url: Optional[str] = None
    scheduled_date: Optional[datetime] = None

class GbpPostScheduleResponse(BaseModel):
    id: UUID
    location_id: UUID
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    media_url: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SeoDashboardData(BaseModel):
    profile: Optional[SeoProfileResponse] = None
    keywords: List[KeywordRankingResponse]
    citations: List[CitationRecordResponse]
    audit: Optional[SeoAuditResult] = None
    maps_rankings: List[CompetitorMapsRankingResponse] = []
    post_schedules: List[GbpPostScheduleResponse] = []
