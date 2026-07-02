from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class GoogleLocationOptionResponse(BaseModel):
    name: str
    title: str


class GoogleIntegrationStatusResponse(BaseModel):
    is_configured: bool
    is_connected: bool
    client_id: Optional[str] = None
    google_account_id: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_error: Optional[str] = None
    last_sync_attempt_at: Optional[datetime] = None
    last_reply_status: Optional[str] = None
    last_reply_error: Optional[str] = None
    last_reply_attempt_at: Optional[datetime] = None
    mapped_location_id: Optional[str] = None
    mapped_google_location_id: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    available_locations: List[GoogleLocationOptionResponse] = []
    sync_failures: int = 0
    next_sync_at: Optional[datetime] = None
    google_api_error: Optional[str] = None


class GoogleSyncResponse(BaseModel):
    status: str
    imported_reviews: int
    skipped_reviews: int
    synced_location_id: str
    google_location_id: str
    last_sync_time: datetime
