from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.core.crypto import EncryptedToken
from app.database import Base
from app.models.base import BaseMixin

class GoogleIntegration(Base, BaseMixin):
    __tablename__ = "google_integrations"

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, unique=True)
    access_token = Column(EncryptedToken, nullable=False)
    refresh_token = Column(EncryptedToken, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    google_account_id = Column(String(255), nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_error = Column(String, nullable=True)
    last_sync_attempt_at = Column(DateTime, nullable=True)
    last_reply_status = Column(String(50), nullable=True)
    last_reply_error = Column(String, nullable=True)
    last_reply_attempt_at = Column(DateTime, nullable=True)
    sync_failures = Column(Integer, default=0, nullable=False)
    next_sync_at = Column(DateTime, nullable=True)

    # Relationships
    client = relationship("Client", backref="google_integration")
