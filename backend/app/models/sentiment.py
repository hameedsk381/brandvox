from sqlalchemy import Column, String, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class SentimentResult(Base, BaseMixin):
    __tablename__ = "sentiment_results"

    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    sentiment = Column(String(50), nullable=False) # positive, negative, neutral, mixed
    confidence = Column(Float, nullable=False)
    emotions = Column(JSON, default=list, nullable=False)

    # Relationships
    review = relationship("Review", back_populates="sentiment_result")

class TopicResult(Base, BaseMixin):
    __tablename__ = "topic_results"

    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(100), nullable=False)
    sub_topic = Column(String(100), nullable=True)
    sentiment = Column(String(50), nullable=True) # positive, negative, neutral

    # Relationships
    review = relationship("Review", back_populates="topic_results")
