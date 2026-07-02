from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Integer, Text
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class WebhookEndpoint(Base, BaseMixin):
    __tablename__ = "webhook_endpoints"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    secret = Column(String(255), nullable=True)
    event_types = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0, nullable=False)

class WebhookDelivery(Base, BaseMixin):
    __tablename__ = "webhook_deliveries"

    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    attempt = Column(Integer, default=1, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
