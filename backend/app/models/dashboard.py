from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Integer
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class Dashboard(Base, BaseMixin):
    __tablename__ = "dashboards"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    layout = Column(JSON, default=list, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
