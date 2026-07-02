from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Any

class PriceRecordCreate(BaseModel):
    price: float
    description: Optional[str] = None
    recorded_at: Optional[datetime] = None

class PriceRecordResponse(BaseModel):
    id: str
    competitor_id: str
    competitor_name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    recorded_at: datetime

class LocationAlertCreate(BaseModel):
    competitor_name: str
    alert_type: str
    description: Optional[str] = None
    source_url: Optional[str] = None

class LocationAlertResponse(BaseModel):
    id: str
    competitor_name: str
    alert_type: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    detected_at: datetime
    is_read: bool

class CompetitorIntelDashboard(BaseModel):
    total_competitors: int
    tracked_prices: int
    active_alerts: int
    price_changes: List[PriceRecordResponse]
    alerts: List[LocationAlertResponse]
    latest_analysis: Any = None

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
