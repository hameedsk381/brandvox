from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from app.database import get_db
from app.schemas.analytics import DashboardResponse, SentimentBreakdownResponse
from app.services.analytics_service import get_dashboard_data, get_sentiment_analytics
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
