from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.api_keys import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse, ApiKeyUpdate
from app.services.api_key_service import create_api_key, list_api_keys, update_api_key, delete_api_key
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

@router.get("", response_model=List[ApiKeyResponse])
async def list_keys(
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    return await list_api_keys(db, current_user.agency_id)

@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    req: ApiKeyCreate,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    key, raw = await create_api_key(db, current_user.agency_id, req.name, req.scopes)
    return ApiKeyCreatedResponse(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        scopes=key.scopes,
        is_active=key.is_active,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at,
        created_at=key.created_at,
        raw_key=raw,
    )

@router.patch("/{key_id}", response_model=ApiKeyResponse)
async def update_key(
    key_id: str,
    req: ApiKeyUpdate,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return await update_api_key(db, current_user.agency_id, key_id, updates)

@router.delete("/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    current_user: User = Depends(RoleChecker(["agency_admin"])),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="No agency associated with user")
    await delete_api_key(db, current_user.agency_id, key_id)
