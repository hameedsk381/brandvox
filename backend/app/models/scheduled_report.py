from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.base import BaseMixin


class ScheduledReport(Base, BaseMixin):
    __tablename__ = "scheduled_reports"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False, default="monthly")
    format = Column(String(20), nullable=False, default="pdf")
    cron_expression = Column(String(100), nullable=False)
    recipients = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
