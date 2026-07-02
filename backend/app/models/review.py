from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class Review(Base, BaseMixin):
    __tablename__ = "reviews"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), default="google", nullable=False)
    source_review_id = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=True)
    author_image_url = Column(String(1024), nullable=True)
    rating = Column(Integer, nullable=False) # 1 to 5
    text = Column(String, nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="reviews")
    replies = relationship("ReviewReply", back_populates="review", cascade="all, delete-orphan")
    sentiment_result = relationship("SentimentResult", back_populates="review", uselist=False, cascade="all, delete-orphan")
    topic_results = relationship("TopicResult", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "source_review_id", name="uq_review_source_id"),
    )

class ReviewReply(Base, BaseMixin):
    __tablename__ = "review_replies"

    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    status = Column(String(50), default="draft", nullable=False) # draft, approved, posted, rejected
    generated_by = Column(String(50), default="ai", nullable=False) # ai, manual
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    review = relationship("Review", back_populates="replies")
    approved_by_user = relationship("User", back_populates="approved_replies")
