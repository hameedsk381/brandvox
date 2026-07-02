from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List
from app.database import get_db
from app.schemas.tenant import (
    AgencyCreate, AgencyResponse, AgencyUpdate,
    ClientCreate, ClientResponse, ClientUpdate,
    LocationCreate, LocationResponse, LocationUpdate,
    AgencyGoogleCredentialsUpdate, AgencyGoogleCredentialsResponse
)
from app.models.tenant import Agency, Client, Location, BrandingConfig
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(tags=["tenants"])

# ----------------- AGENCIES -----------------

@router.get("/agencies", response_model=List[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin"]))
):
    result = await db.execute(select(Agency))
    return result.scalars().all()

@router.post("/agencies", response_model=AgencyResponse)
async def create_agency(
    req: AgencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin"]))
):
    agency = Agency(name=req.name, slug=req.slug, settings=req.settings)
    db.add(agency)
    await db.flush()
    
    branding = BrandingConfig(agency_id=agency.id, company_name=agency.name)
    db.add(branding)
    
    await db.commit()
    await db.refresh(agency)
    return agency

@router.get("/agencies/{agency_id}/google-credentials", response_model=AgencyGoogleCredentialsResponse)
async def get_google_credentials(
    agency_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    if current_user.role != "super_admin" and str(current_user.agency_id) != str(agency_id):
        raise HTTPException(status_code=403, detail="Unauthorized agency context")
        
    result = await db.execute(select(Agency).filter(Agency.id == agency_id))
    agency = result.scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
        
    return AgencyGoogleCredentialsResponse(
        client_id=agency.google_oauth_client_id,
        has_secret=bool(agency.google_oauth_client_secret)
    )

@router.put("/agencies/{agency_id}/google-credentials", response_model=AgencyGoogleCredentialsResponse)
async def update_google_credentials(
    agency_id: UUID,
    req: AgencyGoogleCredentialsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    if current_user.role != "super_admin" and str(current_user.agency_id) != str(agency_id):
        raise HTTPException(status_code=403, detail="Unauthorized agency context")
        
    result = await db.execute(select(Agency).filter(Agency.id == agency_id))
    agency = result.scalars().first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
        
    agency.google_oauth_client_id = req.client_id
    if req.client_secret is not None and req.client_secret.strip() != "":
        agency.google_oauth_client_secret = req.client_secret
    await db.commit()
    
    return AgencyGoogleCredentialsResponse(
        client_id=agency.google_oauth_client_id,
        has_secret=bool(agency.google_oauth_client_secret)
    )


# ----------------- CLIENTS -----------------

@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Client)
    # Scope check
    if current_user.role != "super_admin":
        if current_user.agency_id:
            query = query.filter(Client.agency_id == current_user.agency_id)
        elif current_user.client_id:
            query = query.filter(Client.id == current_user.client_id)
        else:
            return []
            
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/clients", response_model=ClientResponse)
async def create_client(
    req: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    # Verify user manages this agency
    if current_user.role != "super_admin" and current_user.agency_id != req.agency_id:
        raise HTTPException(status_code=403, detail="Unauthorized agency context")
        
    client = Client(agency_id=req.agency_id, name=req.name, industry=req.industry, settings=req.settings)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

# ----------------- LOCATIONS -----------------

@router.get("/locations", response_model=List[LocationResponse])
async def list_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Location)
    # Scope check
    if current_user.role != "super_admin":
        if current_user.location_id:
            query = query.filter(Location.id == current_user.location_id)
        elif current_user.client_id:
            query = query.filter(Location.client_id == current_user.client_id)
        elif current_user.agency_id:
            query = query.join(Client).filter(Client.agency_id == current_user.agency_id)
        else:
            return []
            
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/locations", response_model=LocationResponse)
async def create_location(
    req: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["client_admin"]))
):
    # Verify user manages this client
    if current_user.role != "super_admin":
        if current_user.client_id and current_user.client_id != req.client_id:
            raise HTTPException(status_code=403, detail="Unauthorized client context")
            
    location = Location(
        client_id=req.client_id,
        name=req.name,
        address=req.address,
        google_place_id=req.google_place_id,
        timezone=req.timezone
    )
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location
