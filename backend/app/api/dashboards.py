from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.schemas.dashboards import DashboardCreate, DashboardUpdate, DashboardResponse
from app.models.dashboard import Dashboard
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

@router.get("", response_model=List[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        return []
    result = await db.execute(
        select(Dashboard).filter(
            Dashboard.agency_id == current_user.agency_id,
            (Dashboard.user_id == current_user.id) | (Dashboard.is_shared == True),
        ).order_by(Dashboard.is_default.desc(), Dashboard.created_at.desc())
    )
    return result.scalars().all()

@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    req: DashboardCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    dash = Dashboard(
        agency_id=current_user.agency_id,
        user_id=current_user.id,
        name=req.name,
        description=req.description,
        layout=[w.model_dump() for w in req.layout],
        is_default=req.is_default,
    )
    db.add(dash)
    await db.commit()
    await db.refresh(dash)
    return dash

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dashboard).filter(Dashboard.id == dashboard_id))
    dash = result.scalar_one_or_none()
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dash.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return dash

@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    req: DashboardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dashboard).filter(Dashboard.id == dashboard_id))
    dash = result.scalar_one_or_none()
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dash.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Access denied")
    updates = req.model_dump(exclude_none=True)
    if "layout" in updates and updates["layout"] is not None:
        updates["layout"] = [w.model_dump() for w in updates["layout"]]
    for k, v in updates.items():
        setattr(dash, k, v)
    await db.commit()
    await db.refresh(dash)
    return dash

@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dashboard).filter(Dashboard.id == dashboard_id))
    dash = result.scalar_one_or_none()
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if dash.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(dash)
    await db.commit()
