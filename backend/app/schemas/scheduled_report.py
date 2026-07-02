from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ScheduledReportCreate(BaseModel):
    name: str
    report_type: str = "monthly"
    format: str = "pdf"
    cron_expression: str = "0 8 * * 1"
    recipients: List[str] = []
    is_active: bool = True
    client_id: Optional[str] = None
    location_id: Optional[str] = None


class ScheduledReportUpdate(BaseModel):
    name: Optional[str] = None
    report_type: Optional[str] = None
    format: Optional[str] = None
    cron_expression: Optional[str] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ScheduledReportResponse(BaseModel):
    id: str
    agency_id: str
    client_id: Optional[str] = None
    location_id: Optional[str] = None
    name: str
    report_type: str
    format: str
    cron_expression: str
    recipients: List[str] = []
    is_active: bool
    last_sent_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
