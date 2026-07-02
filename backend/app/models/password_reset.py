from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class PasswordResetToken(Base, BaseMixin):
    __tablename__ = "password_reset_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
