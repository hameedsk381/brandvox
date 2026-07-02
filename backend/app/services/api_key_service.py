import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.api_key import ApiKey

def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def _generate_key() -> Tuple[str, str, str]:
    raw = f"rpk_{secrets.token_urlsafe(32)}"
    prefix = raw[:8]
    h = _hash_key(raw)
    return raw, prefix, h

async def create_api_key(db: AsyncSession, agency_id, name: str, scopes: List[str]) -> tuple:
    raw, prefix, key_hash = _generate_key()
    api_key = ApiKey(
        agency_id=agency_id,
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw

async def list_api_keys(db: AsyncSession, agency_id) -> List[ApiKey]:
    result = await db.execute(
        select(ApiKey).filter(ApiKey.agency_id == agency_id).order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()

async def get_api_key(db: AsyncSession, agency_id, key_id) -> ApiKey:
    result = await db.execute(
        select(ApiKey).filter(ApiKey.id == key_id, ApiKey.agency_id == agency_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

async def update_api_key(db: AsyncSession, agency_id, key_id, updates: dict) -> ApiKey:
    key = await get_api_key(db, agency_id, key_id)
    for field, value in updates.items():
        if value is not None:
            setattr(key, field, value)
    await db.commit()
    await db.refresh(key)
    return key

async def delete_api_key(db: AsyncSession, agency_id, key_id) -> None:
    key = await get_api_key(db, agency_id, key_id)
    await db.delete(key)
    await db.commit()

async def verify_api_key(db: AsyncSession, raw_key: str) -> Optional[ApiKey]:
    key_hash = _hash_key(raw_key)
    result = await db.execute(
        select(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    if not key:
        return None
    if key.expires_at and key.expires_at < datetime.now(timezone.utc):
        return None
    key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return key
