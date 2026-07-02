from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.brand_voice import BrandVoiceProfileResponse, BrandVoiceProfileUpdate
from app.services.reply_service import get_brand_voice_for_client
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/brand-voice", tags=["settings"])

@router.get("/{client_id}", response_model=BrandVoiceProfileResponse)
async def get_brand_voice(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify user access
    if current_user.role != "super_admin":
        if current_user.client_id and current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Unauthorized client voice context")
            
    profile = await get_brand_voice_for_client(db, client_id)
    return profile

@router.put("/{client_id}", response_model=BrandVoiceProfileResponse)
async def update_brand_voice(
    client_id: UUID,
    req: BrandVoiceProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    if current_user.role != "super_admin":
        if current_user.client_id and current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Unauthorized client voice context")
            
    profile = await get_brand_voice_for_client(db, client_id)
    
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    await db.commit()
    await db.refresh(profile)
    return profile
