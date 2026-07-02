from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List
from app.database import get_db
from app.schemas.alert import CrisisAlertResponse, AlertIntegrationResponse, AlertIntegrationCreate
from app.models.tenant import Location
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker, check_location_access
from app.services.alert_service import (
    get_alerts,
    resolve_alert,
    get_integrations,
    upsert_integration
)
from app.models.review import Review

router = APIRouter(prefix="/alerts", tags=["Crisis Alerts"])


@router.get("", response_model=List[CrisisAlertResponse])
async def list_alerts_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    alerts = await get_alerts(db, location_id)
    
    # Enrich with review text and author name for the UI
    enriched_alerts = []
    for alert in alerts:
        res = await db.execute(select(Review.text, Review.author_name, Review.rating).filter(Review.id == alert.review_id))
        row = res.first()
        alert_dict = alert.__dict__.copy()
        if row:
            alert_dict["review_text"] = row[0]
            alert_dict["author_name"] = row[1]
            alert_dict["rating"] = row[2]
        enriched_alerts.append(alert_dict)
        
    return enriched_alerts


@router.patch("/{id}/resolve", response_model=CrisisAlertResponse)
async def resolve_alert_api(
    id: UUID,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager", "customer_support", "branch_manager"]))
):
    await check_location_access(location_id, current_user, db)
    alert = await resolve_alert(db, id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    return alert


@router.get("/integrations", response_model=List[AlertIntegrationResponse])
async def list_integrations_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    return await get_integrations(db, location_id)


@router.post("/integrations", response_model=AlertIntegrationResponse)
async def upsert_integration_api(
    req: AlertIntegrationCreate,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    await check_location_access(location_id, current_user, db)
    return await upsert_integration(db, location_id, req.type, str(req.webhook_url), req.is_active)
