from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any

WIDGET_TYPES = [
    "reputation_score", "avg_rating", "total_reviews", "response_rate",
    "sentiment_distribution", "rating_trend", "recent_reviews",
    "top_topics", "ai_recommendations", "review_volume",
    "forecast_preview", "competitor_overview",
]

class WidgetConfig(BaseModel):
    type: str
    title: str
    width: int = 1
    height: int = 1
    x: int = 0
    y: int = 0
    settings: dict = {}

class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    layout: List[WidgetConfig] = []
    is_default: bool = False

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[List[WidgetConfig]] = None
    is_default: Optional[bool] = None
    is_shared: Optional[bool] = None

class DashboardResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    layout: List[dict]
    is_default: bool
    is_shared: bool
    created_at: datetime

    class Config:
        from_attributes = True
