from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Dict, Any

class ReputationScoreResponse(BaseModel):
    id: UUID
    location_id: UUID
    score_date: date
    overall_score: float
    avg_rating: float
    review_volume: int
    sentiment_score: float
    response_rate: float
    components: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class RatingTrendPoint(BaseModel):
    date: str
    avg_rating: float
    review_count: int

class SentimentDistribution(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    mixed: int = 0

class RecommendationItem(BaseModel):
    id: str
    type: str # warning, info, success, action
    title: str
    description: str
    target_url: Optional[str] = None

class DashboardResponse(BaseModel):
    reputation_score: float
    avg_rating: float
    total_reviews: int
    response_rate: float
    sentiment_score: float # 0.0 to 1.0 (or -1.0 to 1.0)
    review_growth: float # Percentage growth
    rating_trend: List[RatingTrendPoint] = []
    sentiment_distribution: SentimentDistribution
    recent_reviews: List[Any] = [] # List[ReviewResponse] handled dynamically
    ai_recommendations: List[RecommendationItem] = []
    top_topics: List[Dict[str, Any]] = []

class SentimentBreakdownResponse(BaseModel):
    sentiment_distribution: SentimentDistribution
    emotions: Dict[str, int]
    source_distribution: Dict[str, Dict[str, int]] # source -> {positive, negative, etc.}
    location_distribution: Dict[str, Dict[str, int]] # location -> {positive, negative, etc.}
