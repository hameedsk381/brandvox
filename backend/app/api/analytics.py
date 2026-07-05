from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from app.database import get_db
from app.schemas.analytics import ActivationResponse, DashboardResponse, SentimentBreakdownResponse
from app.services.analytics_service import get_dashboard_data, get_sentiment_analytics
from app.models.integration import GoogleIntegration
from app.models.tenant import Agency, Client
from app.models.user import User
from app.core.dependencies import get_current_active_user

router = APIRouter(tags=["analytics"])

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agency_id = current_user.agency_id if current_user.role != "super_admin" else None
    client_id = current_user.client_id if current_user.role not in ["super_admin", "agency_admin"] else None
    location_id = current_user.location_id if current_user.role in ["customer_support", "branch_manager"] else None

    # Load data
    data = await get_dashboard_data(
        db=db,
        agency_id=agency_id,
        client_id=client_id,
        location_id=location_id
    )
    return data

@router.get("/analytics/sentiment", response_model=SentimentBreakdownResponse)
async def get_sentiment_details(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agency_id = current_user.agency_id if current_user.role != "super_admin" else None
    client_id = current_user.client_id if current_user.role not in ["super_admin", "agency_admin"] else None
    location_id = current_user.location_id if current_user.role in ["customer_support", "branch_manager"] else None

    data = await get_sentiment_analytics(
        db=db,
        agency_id=agency_id,
        client_id=client_id,
        location_id=location_id
    )
    return data

@router.get("/analytics/activation", response_model=ActivationResponse)
async def get_activation_kpis(
    agency_id: Optional[UUID] = Query(None, description="super_admin only: inspect another agency"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activation KPIs: time-to-first-sync and time-to-first-AI-reply for an agency."""
    if agency_id is not None and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super_admin may query another agency")

    target_agency_id = agency_id if agency_id is not None else current_user.agency_id
    if target_agency_id is None:
        raise HTTPException(status_code=400, detail="No agency in scope")

    agency = (await db.execute(select(Agency).filter(Agency.id == target_agency_id))).scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    # Earliest Google connection across the agency's clients
    google_connected_at = (
        await db.execute(
            select(func.min(GoogleIntegration.created_at))
            .join(Client, GoogleIntegration.client_id == Client.id)
            .filter(Client.agency_id == agency.id)
        )
    ).scalar()

    def _delta(ts):
        return (ts - agency.created_at).total_seconds() if ts else None

    return ActivationResponse(
        agency_id=agency.id,
        agency_name=agency.name,
        account_created_at=agency.created_at,
        google_connected_at=google_connected_at,
        first_synced_at=agency.first_synced_at,
        first_ai_reply_at=agency.first_ai_reply_at,
        seconds_to_first_sync=_delta(agency.first_synced_at),
        seconds_to_first_ai_reply=_delta(agency.first_ai_reply_at),
    )
