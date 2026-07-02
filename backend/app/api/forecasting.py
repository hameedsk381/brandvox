from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from app.database import get_db
from app.schemas.forecast import ForecastResponse
from app.models.tenant import Location
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.forecasting_service import get_latest_forecast, get_historical_dataset

router = APIRouter(prefix="/forecasting", tags=["forecasting"])

async def check_location_access(location_id: UUID, current_user: User, db: AsyncSession):
    result = await db.execute(select(Location).filter(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    if current_user.role == "super_admin":
        return location
        
    if current_user.role == "agency_admin":
        from app.models.tenant import Client
        c_res = await db.execute(select(Client).filter(Client.id == location.client_id))
        client = c_res.scalar_one_or_none()
        if not client or client.agency_id != current_user.agency_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return location
        
    if current_user.role in ["client_admin", "marketing_manager"]:
        if location.client_id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return location
        
    if current_user.role in ["customer_support", "branch_manager", "read_only"]:
        if current_user.location_id != location_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return location
        
    raise HTTPException(status_code=403, detail="Unauthorized role")

@router.get("", response_model=ForecastResponse)
async def get_forecast_api(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await check_location_access(location_id, current_user, db)
    
    # 1. Fetch AI Forecast (cached or newly generated)
    forecast = await get_latest_forecast(db, location_id)
    
    # 2. Get Historical dataset for plotting
    dataset = await get_historical_dataset(db, location_id)
    
    # 3. Enrich response
    response_data = forecast.__dict__.copy()
    response_data["historical_data"] = dataset
    
    return response_data
