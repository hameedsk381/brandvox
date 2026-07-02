from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Integer, Float
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class SeoProfile(Base, BaseMixin):
    __tablename__ = "seo_profiles"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    gbp_completeness_score = Column(Integer, default=0, nullable=False)
    gbp_missing_fields = Column(JSON, default=list, nullable=False)
    gbp_photo_count = Column(Integer, default=0, nullable=False)
    gbp_post_count = Column(Integer, default=0, nullable=False)
    gbp_response_rate = Column(Float, default=0.0, nullable=False)
    last_audit_at = Column(DateTime(timezone=True), nullable=True)

class KeywordRanking(Base, BaseMixin):
    __tablename__ = "keyword_rankings"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    current_rank = Column(Integer, nullable=True)
    previous_rank = Column(Integer, nullable=True)
    search_volume = Column(String(50), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

class CitationRecord(Base, BaseMixin):
    __tablename__ = "citation_records"

    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    directory_name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True)
    nap_consistent = Column(Boolean, default=True, nullable=False)
    issues = Column(JSON, default=list, nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
