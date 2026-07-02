from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Any

class CompetitorBase(BaseModel):
    name: str
    google_place_id: Optional[str] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorResponse(CompetitorBase):
    id: UUID
    location_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CompetitorReviewResponse(BaseModel):
    id: UUID
    competitor_id: UUID
    author_name: Optional[str] = None
    rating: int
    text: Optional[str] = None
    review_date: datetime
    sentiment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CompetitorAnalysisResponse(BaseModel):
    id: UUID
    location_id: UUID
    analysis_date: date
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CompetitorMetrics(BaseModel):
    name: str
    avg_rating: float
    review_count: int
    sentiment_distribution: Dict[str, int]

class ComparisonAnalyticsResponse(BaseModel):
    client: CompetitorMetrics
    competitors: List[CompetitorMetrics]
