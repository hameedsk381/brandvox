import secrets
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.tenant import Agency, BrandingConfig
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.auth import hash_password, verify_password, create_access_token, validate_password_strength

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def register_user(db: AsyncSession, req: RegisterRequest) -> User:
    existing_user = await get_user_by_email(db, req.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    agency_id = None
    role = "read_only"
    if req.agency_name:
        slug = req.agency_name.lower().replace(" ", "-").replace("/", "")
        new_agency = Agency(name=req.agency_name, slug=slug)
        db.add(new_agency)
        await db.flush()
        
        branding = BrandingConfig(
            agency_id=new_agency.id,
            company_name=req.agency_name
        )
        db.add(branding)
        
        agency_id = new_agency.id
        role = "agency_admin"
        
    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        name=req.name,
        role=role,
        agency_id=agency_id,
        password_changed_at=datetime.now(timezone.utc),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, req: LoginRequest) -> User:
    user = await get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def change_user_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    err = validate_password_strength(new_password)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()

async def create_password_reset_token(db: AsyncSession, email: str) -> Optional[str]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    token = secrets.token_urlsafe(48)
    reset = PasswordResetToken(
        user_id=user.id,
        token=hash_password(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset)
    await db.commit()
    return token

async def verify_reset_token(db: AsyncSession, token: str, new_password: str) -> None:
    all_tokens = await db.execute(select(PasswordResetToken).filter(
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ))
    for reset in all_tokens.scalars().all():
        if verify_password(token, reset.token):
            user_result = await db.execute(select(User).filter(User.id == reset.user_id))
            user = user_result.scalars().first()
            if not user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
            user.hashed_password = hash_password(new_password)
            user.password_changed_at = datetime.now(timezone.utc)
            reset.used = True
            reset.used_at = datetime.now(timezone.utc)
            await db.commit()
            return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token"
    )

def has_admin_role(role: str) -> bool:
    return role in ("super_admin", "agency_admin", "client_admin")
