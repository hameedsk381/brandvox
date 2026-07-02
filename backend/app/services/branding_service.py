from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.tenant import BrandingConfig
from app.schemas.branding import BrandingConfigUpdate

async def get_branding_by_agency(db: AsyncSession, agency_id: UUID) -> BrandingConfig:
    result = await db.execute(select(BrandingConfig).filter(BrandingConfig.agency_id == agency_id))
    config = result.scalars().first()
    if not config:
        # Create a default branding config if not found
        config = BrandingConfig(agency_id=agency_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config

async def update_branding(db: AsyncSession, agency_id: UUID, req: BrandingConfigUpdate) -> BrandingConfig:
    config = await get_branding_by_agency(db, agency_id)
    
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config
