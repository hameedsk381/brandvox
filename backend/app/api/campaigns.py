from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.database import get_db
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignContactCreate, CampaignContactResponse,
    CampaignAnalytics, CampaignSendRequest,
    LeaderboardEntry, GenerationDashboard, FunnelFeedback,
)
from app.services.campaign_service import (
    list_campaigns, get_campaign, create_campaign, update_campaign,
    delete_campaign, get_campaign_analytics, generate_qr_code,
    add_campaign_contacts, list_contacts, send_campaign_contacts,
    get_leaderboard, get_generation_dashboard, record_employee_conversion,
)
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin", "marketing_manager"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    return await list_campaigns(db, current_user.agency_id)

@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign_endpoint(
    req: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin", "marketing_manager"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    return await create_campaign(db, current_user.agency_id, req)

@router.get("/dashboard", response_model=GenerationDashboard)
async def generation_dashboard_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    return await get_generation_dashboard(db, current_user.agency_id)

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard_endpoint(
    location_id: Optional[UUID] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    return await get_leaderboard(db, current_user.agency_id, location_id, days)

@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    campaign = await get_campaign(db, id, current_user.agency_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.patch("/{id}", response_model=CampaignResponse)
async def update_campaign_endpoint(
    id: UUID,
    req: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    campaign = await update_campaign(db, id, current_user.agency_id, req)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.delete("/{id}", status_code=204)
async def delete_campaign_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    deleted = await delete_campaign(db, id, current_user.agency_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")

@router.get("/{id}/qr")
async def generate_qr_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    campaign = await get_campaign(db, id, current_user.agency_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    qr_base64 = await generate_qr_code(campaign)
    return {"qr_code": qr_base64, "campaign_id": str(id)}

@router.get("/{id}/analytics", response_model=CampaignAnalytics)
async def campaign_analytics_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    analytics = await get_campaign_analytics(db, id, current_user.agency_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return analytics

@router.get("/{id}/contacts", response_model=List[CampaignContactResponse])
async def list_contacts_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    campaign = await get_campaign(db, id, current_user.agency_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await list_contacts(db, id)

@router.post("/{id}/contacts", response_model=List[CampaignContactResponse], status_code=201)
async def add_contacts_endpoint(
    id: UUID,
    req: CampaignSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin", "marketing_manager"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    campaign = await get_campaign(db, id, current_user.agency_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await add_campaign_contacts(db, id, req.contacts)

@router.post("/{id}/send")
async def send_campaign_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin", "client_admin", "marketing_manager"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    result = await send_campaign_contacts(db, id, current_user.agency_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed"))
    return result

@router.post("/funnel/feedback")
async def funnel_feedback_endpoint(
    req: FunnelFeedback,
    db: AsyncSession = Depends(get_db),
):
    result = await record_employee_conversion(db, UUID(req.contact_id))
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"success": True, "message": "Feedback recorded"}
