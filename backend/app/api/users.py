from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.schemas.auth import UserResponse, RegisterRequest
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker
from app.core.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    query = select(User)
    
    # Filter users based on scope
    if current_user.role != "super_admin":
        if current_user.agency_id:
            query = query.filter(User.agency_id == current_user.agency_id)
        elif current_user.client_id:
            query = query.filter(User.client_id == current_user.client_id)
        else:
            return [current_user]
            
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=UserResponse)
async def create_user(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    # Verify user exists
    result = await db.execute(select(User).filter(User.email == req.email))
    exist = result.scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="User email already exists")
        
    # Standard role mapping for new users created by admins
    role = "read_only"
    if current_user.role == "agency_admin":
        role = "client_admin"
        
    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        name=req.name,
        role=role,
        agency_id=current_user.agency_id,
        client_id=current_user.client_id,
        location_id=current_user.location_id
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
