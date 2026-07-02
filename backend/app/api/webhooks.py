from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.schemas.webhooks import (
    WebhookEndpointCreate, WebhookEndpointUpdate, WebhookEndpointResponse,
    WebhookDeliveryResponse, EVENT_TYPES,
)
from app.services.webhook_service import (
    list_endpoints, create_endpoint, update_endpoint, delete_endpoint,
    list_deliveries, dispatch_event,
)
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.get("/endpoints", response_model=List[WebhookEndpointResponse])
async def get_endpoints(
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    return await list_endpoints(db, current_user.agency_id)

@router.post("/endpoints", response_model=WebhookEndpointResponse, status_code=201)
async def create_webhook_endpoint(
    req: WebhookEndpointCreate,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    for et in req.event_types:
        if et not in EVENT_TYPES and et != "*":
            raise HTTPException(status_code=400, detail=f"Invalid event type: {et}")
    return await create_endpoint(db, current_user.agency_id, req.model_dump())

@router.patch("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    endpoint_id: UUID,
    req: WebhookEndpointUpdate,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    try:
        return await update_endpoint(db, current_user.agency_id, endpoint_id, req.model_dump(exclude_none=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Endpoint not found")

@router.delete("/endpoints/{endpoint_id}", status_code=204)
async def delete_webhook_endpoint(
    endpoint_id: UUID,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    try:
        await delete_endpoint(db, current_user.agency_id, endpoint_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Endpoint not found")

@router.get("/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_deliveries(
    endpoint_id: Optional[UUID] = None,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated")
    return await list_deliveries(db, current_user.agency_id, endpoint_id, limit)

@router.get("/event-types")
async def get_event_types():
    return EVENT_TYPES
