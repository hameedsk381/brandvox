from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.tenant import Agency, BrandingConfig
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.auth import hash_password, verify_password, create_access_token

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
        
    # Check if we should create an agency
    agency_id = None
    role = "read_only"
    if req.agency_name:
        # User wants to create a new agency, making them agency_admin
        slug = req.agency_name.lower().replace(" ", "-").replace("/", "")
        new_agency = Agency(name=req.agency_name, slug=slug)
        db.add(new_agency)
        await db.flush() # Populate new_agency.id
        
        # Create default branding config
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
        agency_id=agency_id
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
