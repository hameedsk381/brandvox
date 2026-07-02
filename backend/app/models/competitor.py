from sqlalchemy import Column, String, ForeignKey, Integer, Text, DateTime, Date, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class Competitor(Base, BaseMixin):
    __tablename__ = "competitors"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    google_place_id = Column(String(255), nullable=True)

    # Relationships
    location = relationship("Location", backref="competitors")
    reviews = relationship("CompetitorReview", back_populates="competitor", cascade="all, delete-orphan")

class CompetitorReview(Base, BaseMixin):
    __tablename__ = "competitor_reviews"

    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255), nullable=True)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    review_date = Column(DateTime, nullable=False)
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral, mixed

    # Relationships
    competitor = relationship("Competitor", back_populates="reviews")

class CompetitorAnalysis(Base, BaseMixin):
    __tablename__ = "competitor_analyses"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    analysis_date = Column(Date, nullable=False)
    strengths = Column(JSON, default=list, nullable=False)        # JSON array of strings
    weaknesses = Column(JSON, default=list, nullable=False)       # JSON array of strings
    opportunities = Column(JSON, default=list, nullable=False)    # JSON array of strings
    summary = Column(Text, nullable=True)

    # Relationships
    location = relationship("Location", backref="competitor_analyses")

class CompetitorMapsRanking(Base, BaseMixin):
    __tablename__ = "competitor_maps_rankings"

    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    rank = Column(Integer, nullable=True)
    previous_rank = Column(Integer, nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    competitor = relationship("Competitor", backref="maps_rankings")

class GbpPostSchedule(Base, BaseMixin):
    __tablename__ = "gbp_post_schedules"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # photo, post, offer, event
    title = Column(String(255), nullable=True)
    description = Column(String(2000), nullable=True)
    media_url = Column(String(1024), nullable=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

class CompetitorPriceRecord(Base, BaseMixin):
    __tablename__ = "competitor_price_records"

    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=True)
    description = Column(String(500), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

    competitor = relationship("Competitor", backref="prices")

class CompetitorLocationAlert(Base, BaseMixin):
    __tablename__ = "competitor_location_alerts"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    competitor_name = Column(String(255), nullable=False)
    alert_type = Column(String(50), nullable=False)  # new_location, campaign, expansion
    description = Column(String(500), nullable=True)
    source_url = Column(String(1024), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
