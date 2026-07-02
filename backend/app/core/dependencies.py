from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.core.auth import decode_access_token
from app.core.permissions import has_role_permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> User:
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
        
    # Check subscription status
    if agency.subscription_status == "active":
        return current_user
        
    # Check trial
    if agency.trial_ends_at and agency.trial_ends_at > datetime.utcnow():
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="Active subscription or trial required for this operation."
    )

