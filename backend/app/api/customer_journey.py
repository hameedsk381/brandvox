from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.customer_journey import CustomerProfile, Touchpoint, SupportTicket, OrderRecord, EmailFeedback
from app.models.review import Review
from app.models.chat import ChatSession
from app.models.tenant import Location, Client
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker
from app.services.intelligence_service import (
    import_crm_csv, import_orders_csv, import_feedback_csv,
    run_segmentation, get_segmentation_summary,
    run_root_cause_analysis, get_enhanced_funnel,
)
from pydantic import BaseModel

router = APIRouter(prefix="/customer-journey", tags=["customer-journey"])

class TouchpointCreate(BaseModel):
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    touchpoint_type: str
    channel: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = {}

class FunnelResponse(BaseModel):
    total_customers: int
    reviewed: int
    chatted: int
    ticketed: int
    positive_sentiment: int
    repeat_visitors: int
    segment_breakdown: dict = {}
    total_revenue: float = 0.0

@router.post("/touchpoints", status_code=201)
async def record_touchpoint(
    req: TouchpointCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    customer_id = None
    if req.customer_email:
        result = await db.execute(
            select(CustomerProfile).filter(
                CustomerProfile.agency_id == current_user.agency_id,
                CustomerProfile.email == req.customer_email,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = CustomerProfile(
                agency_id=current_user.agency_id,
                client_id=current_user.client_id,
                email=req.customer_email,
                name=req.customer_name,
                last_activity_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            await db.flush()
        customer_id = profile.id
    tp = Touchpoint(
        agency_id=current_user.agency_id,
        client_id=current_user.client_id,
        customer_id=customer_id,
        touchpoint_type=req.touchpoint_type,
        channel=req.channel,
        description=req.description,
        custom_metadata=req.custom_metadata,
    )
    db.add(tp)
    await db.commit()
    return {"detail": "Touchpoint recorded"}

@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    days: int = 90,
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await get_enhanced_funnel(db, current_user.agency_id, days)
    return result

@router.get("/tickets", status_code=200)
async def list_tickets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50,
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    query = select(SupportTicket).filter(SupportTicket.agency_id == current_user.agency_id)
    if status:
        query = query.filter(SupportTicket.status == status)
    query = query.order_by(SupportTicket.created_at.desc()).limit(limit)
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [{
        "id": str(t.id),
        "subject": t.subject,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "source": t.source,
        "created_at": str(t.created_at),
        "resolved_at": str(t.resolved_at) if t.resolved_at else None,
    } for t in tickets]

@router.patch("/tickets/{ticket_id}", status_code=200)
async def update_ticket(
    ticket_id: UUID,
    status: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SupportTicket).filter(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = status
    if status == "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"detail": "Ticket updated"}

# ── Data Import Endpoints ──────────────────────────────────────────────

@router.post("/import/crm")
async def import_crm(
    csv_data: str = Body(..., embed=True),
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await import_crm_csv(db, current_user.agency_id, csv_data)
    return result

@router.post("/import/orders")
async def import_orders(
    csv_data: str = Body(..., embed=True),
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await import_orders_csv(db, current_user.agency_id, csv_data)
    return result

@router.post("/import/feedback")
async def import_feedback(
    csv_data: str = Body(..., embed=True),
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await import_feedback_csv(db, current_user.agency_id, csv_data)
    return result

# ── Segmentation ───────────────────────────────────────────────────────

@router.post("/segment")
async def trigger_segmentation(
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await run_segmentation(db, current_user.agency_id)
    return result

@router.get("/segments")
async def get_segments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    return await get_segmentation_summary(db, current_user.agency_id)

# ── AI Root-Cause Analysis ─────────────────────────────────────────────

@router.post("/analyze")
async def trigger_analysis(
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    result = await run_root_cause_analysis(db, current_user.agency_id)
    return result

@router.get("/profiles")
async def list_profiles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    segment: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    query = select(CustomerProfile).filter(CustomerProfile.agency_id == current_user.agency_id)
    if segment:
        query = query.filter(CustomerProfile.segment == segment)
    query = query.order_by(CustomerProfile.last_activity_at.desc().nullslast()).limit(limit)
    result = await db.execute(query)
    profiles = result.scalars().all()
    return [{
        "id": str(p.id),
        "email": p.email,
        "name": p.name,
        "phone": p.phone,
        "total_orders": p.total_orders,
        "total_spent": p.total_spent,
        "lifetime_value": p.lifetime_value,
        "segment": p.segment,
        "churn_risk_score": p.churn_risk_score,
        "last_activity_at": str(p.last_activity_at) if p.last_activity_at else None,
        "tags": p.tags,
    } for p in profiles]
