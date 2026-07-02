from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List
from app.database import get_db
from app.schemas.brand_voice import SmartRuleResponse, SmartRuleCreate, SmartRuleUpdate
from app.models.brand_voice import SmartRule
from app.models.user import User
from app.services.audit_service import audit_service
from app.core.dependencies import get_current_active_user, RoleChecker
from fastapi import Request

router = APIRouter(prefix="/smart-rules", tags=["settings"])

@router.get("/{location_id}", response_model=List[SmartRuleResponse])
async def list_smart_rules(
    location_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "super_admin":
        if current_user.location_id and current_user.location_id != location_id:
            raise HTTPException(status_code=403, detail="Unauthorized location context")
            
    result = await db.execute(select(SmartRule).filter(SmartRule.location_id == location_id))
    rules = result.scalars().all()
    
    # If no rules exist, initialize defaults
    if not rules:
        defaults = [
            SmartRule(location_id=location_id, min_rating=5, max_rating=5, action="auto_reply"),
            SmartRule(location_id=location_id, min_rating=4, max_rating=4, action="auto_reply"),
            SmartRule(location_id=location_id, min_rating=3, max_rating=3, action="approval_required"),
            SmartRule(location_id=location_id, min_rating=2, max_rating=2, action="escalate"),
            SmartRule(location_id=location_id, min_rating=1, max_rating=1, action="never_auto"),
        ]
        for d in defaults:
            db.add(d)
        await db.commit()
        
        result = await db.execute(select(SmartRule).filter(SmartRule.location_id == location_id))
        rules = result.scalars().all()
        
    return rules

@router.put("/{location_id}", response_model=List[SmartRuleResponse])
async def update_smart_rules(
    location_id: UUID,
    req_rules: List[SmartRuleUpdate],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    if current_user.role != "super_admin":
        if current_user.location_id and current_user.location_id != location_id:
            raise HTTPException(status_code=403, detail="Unauthorized location context")
            
    # Remove existing rules
    from sqlalchemy import delete
    await db.execute(delete(SmartRule).where(SmartRule.location_id == location_id))
    
    # Insert new ones
    for rule_data in req_rules:
        # Pydantic lists don't always have location_id, we inject it
        db_rule = SmartRule(
            location_id=location_id,
            min_rating=rule_data.min_rating,
            max_rating=rule_data.max_rating,
            action=rule_data.action,
            notify_roles=rule_data.notify_roles or [],
            is_active=rule_data.is_active if rule_data.is_active is not None else True
        )
        db.add(db_rule)
        
    if current_user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=current_user.agency_id,
            action="smart_rules.updated",
            resource_type="SmartRule",
            resource_id=str(location_id),
            user_id=current_user.id,
            details={"rule_count": len(req_rules)},
            request=request
        )
        
    await db.commit()
    
    result = await db.execute(select(SmartRule).filter(SmartRule.location_id == location_id))
    return result.scalars().all()
