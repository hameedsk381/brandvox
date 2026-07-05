from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Location
from app.core.auth import decode_access_token
from app.core.permissions import has_role_permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
        
    # Query user from DB
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_or_api_key(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        from app.services.api_key_service import verify_api_key
        key = await verify_api_key(db, api_key_header)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        from app.models.tenant import Agency
        result = await db.execute(select(Agency).filter(Agency.id == key.agency_id))
        agency = result.scalar_one_or_none()
        if not agency:
            raise HTTPException(status_code=404, detail="Agency not found")
        admin_result = await db.execute(
            select(User).filter(User.agency_id == key.agency_id, User.role == "agency_admin")
        )
        admin = admin_result.scalars().first()
        if not admin:
            raise HTTPException(status_code=403, detail="No admin user for agency")
        return admin

    if token:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a Bearer token or X-API-Key header.",
    )


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # Check if user role matches or is super_admin
        if current_user.role == "super_admin":
            return current_user
            
        # Check if user has permission
        for role in self.allowed_roles:
            if has_role_permission(current_user.role, role):
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role."
        )

async def require_active_subscription(
    current_user: User,
    db: AsyncSession,
) -> User:
    """Standalone subscription check (no Depends). Can be called from middleware or endpoints."""
    from app.models.tenant import Agency
    from datetime import datetime

    if current_user.role == "super_admin":
        return current_user

    if not current_user.agency_id:
        return current_user

    result = await db.execute(select(Agency).filter(Agency.id == current_user.agency_id))
    agency = result.scalars().first()

    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    if agency.subscription_status == "active":
        return current_user

    if agency.trial_ends_at and agency.trial_ends_at > datetime.utcnow():
        return current_user

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="Active subscription or trial required for this operation."
    )


class SubscriptionRequired:
    """FastAPI dependency that wraps require_active_subscription for endpoint use."""
    async def __call__(self, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> User:
        return await require_active_subscription(current_user, db)


async def check_location_access(location_id: UUID, current_user: User, db: AsyncSession) -> Location:
    """Shared helper to verify the current user has access to a location.
    Returns the Location or raises 403/404."""
    from app.models.tenant import Client

    result = await db.execute(select(Location).filter(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    if current_user.role == "super_admin":
        return location

    if current_user.role == "agency_admin":
        c_res = await db.execute(select(Client).filter(Client.id == location.client_id))
        client = c_res.scalar_one_or_none()
        if not client or client.agency_id != current_user.agency_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location

    if current_user.role in ["client_admin", "marketing_manager"]:
        if location.client_id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location

    if current_user.role in ["customer_support", "branch_manager", "read_only"]:
        if current_user.location_id != location_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        return location

    raise HTTPException(status_code=403, detail="Unauthorized role")


async def check_review_access(review_id: UUID, current_user: User, db: AsyncSession):
    """Verify the current user has access to a review via its location.
    Returns the Review or raises 403/404."""
    from app.models.review import Review

    result = await db.execute(select(Review).filter(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await check_location_access(review.location_id, current_user, db)
    return review


async def verify_client_access(client_id: UUID, current_user: User, db: AsyncSession) -> None:
    """Verify the current user has access to a client. Raises 403 if not."""
    from app.models.tenant import Client

    if current_user.role == "super_admin":
        return

    result = await db.execute(select(Client).filter(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if current_user.role == "agency_admin":
        if client.agency_id != current_user.agency_id:
            raise HTTPException(status_code=403, detail="Access denied to this client")
        return

    if current_user.role in ["client_admin", "marketing_manager"]:
        if client.id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied to this client")
        return

    raise HTTPException(status_code=403, detail="Unauthorized role")

