from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class BrandVoiceProfile(Base, BaseMixin):
    __tablename__ = "brand_voice_profiles"

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False)
    tone = Column(String(50), default="professional", nullable=False) # friendly, professional, premium, medical, hospitality, corporate, casual
    vocabulary_notes = Column(String, nullable=True)
    greeting_style = Column(String(255), nullable=True)
    closing_style = Column(String(255), nullable=True)
    example_replies = Column(JSON, default=list, nullable=False)
    personality_traits = Column(JSON, default=list, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="brand_voice")

class SmartRule(Base, BaseMixin):
    __tablename__ = "smart_rules"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    min_rating = Column(Integer, nullable=False)
    max_rating = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False) # auto_reply, approval_required, escalate, never_auto
    notify_roles = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="smart_rules")
