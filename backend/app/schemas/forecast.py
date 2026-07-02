from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ForecastHistoricalDataPoint(BaseModel):
    month: str # e.g., "Jan 2026"
    average_rating: float
    review_volume: int

class ForecastResponse(BaseModel):
    id: UUID
    location_id: UUID
    forecast_date: datetime
    
    predicted_rating: float
    predicted_volume: int
    churn_risk_score: int
    
    reputation_risks: List[str]
    seasonal_trends: List[str]
    actionable_advice: str
    
    historical_data: Optional[List[ForecastHistoricalDataPoint]] = None
    
    class Config:
        from_attributes = True
