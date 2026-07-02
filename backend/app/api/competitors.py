from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional
from app.database import get_db
from app.schemas.competitor import (
    CompetitorResponse, CompetitorCreate, ComparisonAnalyticsResponse,
    CompetitorAnalysisResponse, PriceRecordResponse, LocationAlertResponse,
)
from app.models.tenant import Location
from app.models.competitor import Competitor
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker, check_location_access
from app.services.competitor_service import (
    add_competitor,
    delete_competitor,
    get_competitors,
    get_competitor_analytics,
    run_competitor_ai_analysis,
    get_latest_competitor_analysis,
    record_competitor_price,
    get_competitor_prices,
    get_all_price_changes,
    create_location_alert,
    list_location_alerts,
    mark_alert_read,
    generate_weekly_competitor_report,
)

router = APIRouter(prefix="/competitors", tags=["Competitor Intelligence"])


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

@router.get("/prices", response_model=List[PriceRecordResponse])
async def get_prices(
    competitor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    comp = await db.execute(select(Competitor).filter(Competitor.id == competitor_id))
    comp_data = comp.scalar_one_or_none()
    if not comp_data:
        raise HTTPException(status_code=404, detail="Competitor not found")
    await check_location_access(comp_data.location_id, current_user, db)
    records = await get_competitor_prices(db, competitor_id)
    return [{
        "id": str(r.id),
        "competitor_id": str(r.competitor_id),
        "price": r.price,
        "description": r.description,
        "recorded_at": r.recorded_at,
    } for r in records]

@router.post("/prices", response_model=PriceRecordResponse, status_code=201)
async def add_price(
    competitor_id: UUID = Query(...),
    price: float = Query(...),
    description: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"])),
):
    comp = await db.execute(select(Competitor).filter(Competitor.id == competitor_id))
    comp_data = comp.scalar_one_or_none()
    if not comp_data:
        raise HTTPException(status_code=404, detail="Competitor not found")
    await check_location_access(comp_data.location_id, current_user, db)
    record = await record_competitor_price(db, competitor_id, price, description)
    return {
        "id": str(record.id),
        "competitor_id": str(record.competitor_id),
        "competitor_name": comp_data.name,
        "price": record.price,
        "description": record.description,
        "recorded_at": record.recorded_at,
    }

@router.get("/price-changes", response_model=List[PriceRecordResponse])
async def get_price_changes(
    location_id: UUID = Query(...),
    days: int = Query(default=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await get_all_price_changes(db, location_id, days)

@router.get("/alerts", response_model=List[LocationAlertResponse])
async def get_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    unread_only: bool = Query(default=False),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    alerts = await list_location_alerts(db, current_user.agency_id, unread_only)
    return [{
        "id": str(a.id),
        "competitor_name": a.competitor_name,
        "alert_type": a.alert_type,
        "description": a.description,
        "source_url": a.source_url,
        "detected_at": a.detected_at,
        "is_read": a.is_read,
    } for a in alerts]

@router.post("/alerts", response_model=LocationAlertResponse, status_code=201)
async def add_alert(
    competitor_name: str = Query(...),
    alert_type: str = Query(...),
    description: Optional[str] = Query(default=None),
    source_url: Optional[str] = Query(default=None),
    current_user: User = Depends(RoleChecker(["marketing_manager"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    alert = await create_location_alert(db, current_user.agency_id, competitor_name, alert_type, description, source_url)
    return {
        "id": str(alert.id),
        "competitor_name": alert.competitor_name,
        "alert_type": alert.alert_type,
        "description": alert.description,
        "source_url": alert.source_url,
        "detected_at": alert.detected_at,
        "is_read": alert.is_read,
    }

@router.patch("/alerts/{alert_id}/read")
async def read_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    success = await mark_alert_read(db, alert_id, current_user.agency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"detail": "Alert marked as read"}

@router.get("/weekly-report")
async def weekly_report(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await generate_weekly_competitor_report(db, location_id)
