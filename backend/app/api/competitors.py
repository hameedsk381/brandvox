from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional
from app.database import get_db
from app.schemas.competitor import CompetitorResponse, CompetitorCreate, ComparisonAnalyticsResponse, CompetitorAnalysisResponse
from app.models.tenant import Location
from app.models.competitor import Competitor
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker
from app.services.competitor_service import (
    add_competitor,
    delete_competitor,
    get_competitors,
    get_competitor_analytics,
    run_competitor_ai_analysis,
    get_latest_competitor_analysis
)

router = APIRouter(prefix="/competitors", tags=["Competitor Intelligence"])

async def check_location_access(location_id: UUID, current_user: User, db: AsyncSession):
    """Helper to check if the current user has access to the specified location."""
    result = await db.execute(select(Location).filter(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    if current_user.role == "super_admin":
        return location
        
    if current_user.role == "agency_admin":
        # Check if client belongs to their agency
        from app.models.tenant import Client
        c_res = await db.execute(select(Client).filter(Client.id == location.client_id))
        client = c_res.scalar_one_or_none()
        if not client or client.agency_id != current_user.agency_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location
        
    if current_user.role in ["client_admin", "marketing_manager"]:
        if location.client_id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location
        
    if current_user.role in ["customer_support", "branch_manager", "read_only"]:
        if current_user.location_id != location_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location
        
    raise HTTPException(status_code=403, detail="Unauthorized role")


@router.get("", response_model=List[CompetitorResponse])
async def list_competitors_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    return await get_competitors(db, location_id)


@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def add_competitor_api(
    req: CompetitorCreate,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    await check_location_access(location_id, current_user, db)
    return await add_competitor(db, location_id, req.name, req.google_place_id)


@router.delete("/{id}")
async def delete_competitor_api(
    id: UUID,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    await check_location_access(location_id, current_user, db)
    success = await delete_competitor(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "success", "message": "Competitor deleted"}


@router.get("/analytics", response_model=ComparisonAnalyticsResponse)
async def get_competitor_analytics_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    return await get_competitor_analytics(db, location_id)


@router.get("/analysis", response_model=Optional[CompetitorAnalysisResponse])
async def get_latest_competitor_analysis_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    return await get_latest_competitor_analysis(db, location_id)


@router.post("/analyze", response_model=CompetitorAnalysisResponse)
async def trigger_competitor_analysis_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    await check_location_access(location_id, current_user, db)
    return await run_competitor_ai_analysis(db, location_id)
