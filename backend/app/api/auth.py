from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, authenticate_user
from app.services.audit_service import audit_service
from app.core.dependencies import get_current_active_user
from app.core.auth import create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, req)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, req)
    
    if user and user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=user.agency_id,
            action="user.login",
            resource_type="User",
            resource_id=str(user.id),
            user_id=user.id,
            details={"email": user.email},
            request=request
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
