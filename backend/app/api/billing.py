from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.tenant import Agency
from app.core.dependencies import get_current_active_user, RoleChecker
from app.services.billing_service import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])

class CheckoutRequest(BaseModel):
    plan_id: str

@router.get("/status")
async def get_billing_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")

    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()
    
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    return {
        "subscription_plan": agency.subscription_plan,
        "subscription_status": agency.subscription_status,
        "trial_ends_at": agency.trial_ends_at,
        "is_trial_active": agency.trial_ends_at and agency.trial_ends_at > datetime.utcnow()
    }

@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")

    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()

    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    order = await billing_service.create_checkout_session(agency, req.plan_id)
    return {"order": order}

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    payload = await request.json()
    await billing_service.handle_webhook(db, payload)
    return {"status": "ok"}
