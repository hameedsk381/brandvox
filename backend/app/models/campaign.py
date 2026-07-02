from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Integer
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class ReviewCampaign(Base, BaseMixin):
    __tablename__ = "review_campaigns"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # qr, nfc, sms, email, whatsapp
    target_url = Column(String(1024), nullable=True)
    redirect_url = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    total_sent = Column(Integer, default=0, nullable=False)
    total_opened = Column(Integer, default=0, nullable=False)
    total_converted = Column(Integer, default=0, nullable=False)

class CampaignContact(Base, BaseMixin):
    __tablename__ = "campaign_contacts"

    campaign_id = Column(UUID(as_uuid=True), ForeignKey("review_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient = Column(String(255), nullable=True)
    channel = Column(String(50), nullable=True)  # sms, email, whatsapp
    status = Column(String(50), default="pending", nullable=False)  # pending, sent, opened, converted
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    employee_name = Column(String(255), nullable=True)

class EmployeeLeaderboard(Base, BaseMixin):
    __tablename__ = "employee_leaderboard"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    employee_name = Column(String(255), nullable=False)
    reviews_generated = Column(Integer, default=0, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
