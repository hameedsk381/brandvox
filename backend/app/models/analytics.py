from sqlalchemy import Column, ForeignKey, Float, Integer, Date, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class ReputationScore(Base, BaseMixin):
    __tablename__ = "reputation_scores"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    score_date = Column(Date, nullable=False)
    overall_score = Column(Float, nullable=False) # 0 to 100
    avg_rating = Column(Float, nullable=False)
    review_volume = Column(Integer, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    response_rate = Column(Float, nullable=False)
    components = Column(JSON, default=dict, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="reputation_scores")

    __table_args__ = (
        UniqueConstraint("location_id", "score_date", name="uq_location_score_date"),
    )
