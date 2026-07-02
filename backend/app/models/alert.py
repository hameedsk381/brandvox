import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base

class AlertSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"

class AlertCategory(str, enum.Enum):
    pr_crisis = "pr_crisis"
    health_safety = "health_safety"
    legal = "legal"
    spam = "spam"
    fake_review = "fake_review"

class AlertStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    ignored = "ignored"

class IntegrationType(str, enum.Enum):
    slack = "slack"
    teams = "teams"
    email = "email"

class AlertIntegration(Base):
    __tablename__ = "alert_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(IntegrationType), nullable=False)
    webhook_url = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    category = Column(SQLEnum(AlertCategory), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.open, nullable=False, index=True)
    
    analysis_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
