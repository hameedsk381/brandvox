from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.tenant import Agency
from app.core.dependencies import get_current_active_user, RoleChecker
from app.services.billing_service import billing_service
from app.schemas.billing import CheckoutRequest, BillingStatusResponse, BillingUpdateRequest, PLANS

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")
    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    now = datetime.now(timezone.utc)
    trial_active = bool(agency.trial_ends_at and agency.trial_ends_at.replace(tzinfo=timezone.utc) > now) if agency.trial_ends_at else False
    return BillingStatusResponse(
        subscription_plan=agency.subscription_plan,
        subscription_status=agency.subscription_status,
        trial_ends_at=agency.trial_ends_at,
        is_trial_active=trial_active or agency.subscription_status == "active",
    )

@router.get("/plans")
async def list_plans():
    return [{"id": k, "name": v["name"], "amount": v["amount"], "features": v["features"]} for k, v in PLANS.items()]

@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")
    if req.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {req.plan_id}")
    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    order = await billing_service.create_checkout_session(agency, req.plan_id)
    return {"order": order, "key_id": billing_service.key_id or ""}

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None),
):
    payload = await request.json()
    await billing_service.handle_webhook(db, payload, x_razorpay_signature)
    return {"status": "ok"}

@router.patch("/update")
async def update_billing(
    req: BillingUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"])),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")
    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    updates = req.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(agency, k, v)
    await db.commit()
    return {"detail": "Billing updated"}
