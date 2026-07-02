from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class ApiKey(Base, BaseMixin):
    __tablename__ = "api_keys"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(8), nullable=False)
    key_hash = Column(String(255), nullable=False)
    scopes = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
