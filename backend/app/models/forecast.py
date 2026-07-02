import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer, JSON, Uuid as UUID
from app.database import Base

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    forecast_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    predicted_rating = Column(Float, nullable=False)
    predicted_volume = Column(Integer, nullable=False)
    churn_risk_score = Column(Integer, nullable=False) # 0-100
    
    reputation_risks = Column(JSON, nullable=False, default=list) # List of strings
    seasonal_trends = Column(JSON, nullable=False, default=list) # List of strings
    
    actionable_advice = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
