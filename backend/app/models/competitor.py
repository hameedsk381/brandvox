from sqlalchemy import Column, String, ForeignKey, Integer, Text, DateTime, Date, JSON
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
