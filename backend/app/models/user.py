from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class User(Base, BaseMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="read_only", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # MFA fields
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)

    # Password reset tracking
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Scopes
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    agency = relationship("Agency", back_populates="users")
    client = relationship("Client", back_populates="users")
    location = relationship("Location", back_populates="users")
    approved_replies = relationship("ReviewReply", back_populates="approved_by_user")
