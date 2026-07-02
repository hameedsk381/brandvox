from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Integer, Float
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class CustomerProfile(Base, BaseMixin):
    __tablename__ = "customer_profiles"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    total_orders = Column(Integer, default=0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    lifetime_value = Column(Float, default=0.0, nullable=False)
    segment = Column(String(50), nullable=True)
    churn_risk_score = Column(Float, default=0.0, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    custom_metadata = Column("metadata", JSON, default=dict, nullable=False)

class Touchpoint(Base, BaseMixin):
    __tablename__ = "touchpoints"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    touchpoint_type = Column(String(100), nullable=False)
    channel = Column(String(50), nullable=True)
    description = Column(String(500), nullable=True)
    custom_metadata = Column("metadata", JSON, default=dict, nullable=False)

class SupportTicket(Base, BaseMixin):
    __tablename__ = "support_tickets"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(500), nullable=False)
    description = Column(String(2000), nullable=True)
    status = Column(String(50), default="open", nullable=False)
    priority = Column(String(20), default="normal", nullable=False)
    source = Column(String(50), default="chat", nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class OrderRecord(Base, BaseMixin):
    __tablename__ = "order_records"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    external_order_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(500), nullable=True)
    custom_metadata = Column("metadata", JSON, default=dict, nullable=False)

class EmailFeedback(Base, BaseMixin):
    __tablename__ = "email_feedback"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(500), nullable=True)
    body = Column(String(5000), nullable=True)
    sentiment = Column(String(50), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False)
