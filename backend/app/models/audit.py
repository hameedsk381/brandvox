from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class AuditLog(Base, BaseMixin):
    __tablename__ = "audit_logs"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)

    # Relationships
    agency = relationship("Agency")
    user = relationship("User")
