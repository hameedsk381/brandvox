from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.branding import BrandingConfigResponse, BrandingConfigUpdate
from app.services.branding_service import get_branding_by_agency, update_branding
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/branding", tags=["settings"])

@router.get("/{agency_id}", response_model=BrandingConfigResponse)
async def get_branding(
    agency_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "super_admin":
        if current_user.agency_id and current_user.agency_id != agency_id:
            raise HTTPException(status_code=403, detail="Unauthorized agency context")
            
    config = await get_branding_by_agency(db, agency_id)
    return config

@router.put("/{agency_id}", response_model=BrandingConfigResponse)
async def update_agency_branding(
    agency_id: UUID,
    req: BrandingConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    if current_user.role != "super_admin":
        if current_user.agency_id and current_user.agency_id != agency_id:
            raise HTTPException(status_code=403, detail="Unauthorized agency context")
            
    config = await update_branding(db, agency_id, req)
    return config
