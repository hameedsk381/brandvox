from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from datetime import datetime, timedelta
from jose import JWTError, jwt as jose_jwt
from app.config import get_settings
from app.database import get_db
from app.models.integration import GoogleIntegration
from app.core.dependencies import get_current_active_user, verify_client_access, check_location_access
from app.models.user import User
from app.schemas.integration import GoogleIntegrationStatusResponse, GoogleLocationOptionResponse, GoogleSyncResponse
from app.services.google_integration_service import (
    build_google_integration_status,
    get_client_integration,
    get_client_with_agency,
    import_google_reviews_for_location,
    list_google_locations_for_client,
)
import uuid

router = APIRouter(prefix="/integrations/google", tags=["integrations"])

OAUTH_STATE_PURPOSE = "google_oauth_state"
OAUTH_STATE_EXPIRY_MINUTES = 10


def _redirect_uri() -> str:
    return get_settings().FRONTEND_URL.rstrip("/") + "/dashboard/integrations"


def create_oauth_state(client_id: str) -> str:
    """Signed short-lived state token: binds the OAuth callback to the client
    it was initiated for and prevents CSRF (attacker-supplied callbacks)."""
    settings = get_settings()
    return jose_jwt.encode(
        {
            "purpose": OAUTH_STATE_PURPOSE,
            "client_id": client_id,
            "nonce": str(uuid.uuid4()),
            "exp": datetime.utcnow() + timedelta(minutes=OAUTH_STATE_EXPIRY_MINUTES),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_oauth_state(state: str) -> str:
    """Validate the state token and return the client_id it was issued for."""
    settings = get_settings()
    try:
        payload = jose_jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state. Restart the connection flow.")
    if payload.get("purpose") != OAUTH_STATE_PURPOSE or not payload.get("client_id"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Restart the connection flow.")
    return payload["client_id"]


async def get_agency_credentials(db: AsyncSession, client_id: str) -> tuple[str, str]:
    """Helper to fetch agency credentials for a given client."""
    try:
        client = await get_client_with_agency(db, client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID")
    except LookupError:
        raise HTTPException(status_code=404, detail="Client or Agency not found")

    agency = client.agency
    if not agency.google_oauth_client_id or not agency.google_oauth_client_secret:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth credentials are not configured for this Agency. Please configure them in Settings."
        )

    return agency.google_oauth_client_id, agency.google_oauth_client_secret


@router.get("/auth-url")
async def get_google_auth_url(client_id: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Get the Google OAuth2 authorization URL dynamically based on Agency credentials."""
    client_id_val, _ = await get_agency_credentials(db, client_id)

    # Verify authorization
    if current_user.role != "super_admin":
        client_uuid_check = uuid.UUID(client_id)
        await verify_client_access(client_uuid_check, current_user, db)

    state_token = create_oauth_state(client_id)
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id_val}&"
        f"redirect_uri={_redirect_uri()}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/business.manage&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={state_token}"
    )
    return {"url": auth_url}

@router.post("/callback")
async def google_auth_callback(code: str, state: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Exchange code for tokens using Agency credentials and save to DB."""
    client_id = decode_oauth_state(state)
    client_id_val, client_secret_val = await get_agency_credentials(db, client_id)

    if current_user.role != "super_admin":
        client_uuid_check = uuid.UUID(client_id)
        await verify_client_access(client_uuid_check, current_user, db)

    # In test mode, we'll mock the token exchange if they use test-client-id
    if client_id_val == "test-client-id":
        access_token = "mock-access-token"
        refresh_token = "mock-refresh-token"
        expires_in = 3600
    else:
        # Real token exchange
        async with httpx.AsyncClient() as httpx_client:
            resp = await httpx_client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": client_id_val,
                "client_secret": client_secret_val,
                "redirect_uri": _redirect_uri(),
                "grant_type": "authorization_code"
            })
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange token with Google")
            data = resp.json()
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token", "")
            expires_in = data["expires_in"]

    # Save integration
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID")
    else:
        result = await db.execute(select(GoogleIntegration).filter(GoogleIntegration.client_id == client_uuid))
        integration = result.scalars().first()

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    if integration:
        integration.access_token = access_token
        if refresh_token:
            integration.refresh_token = refresh_token
        integration.expires_at = expires_at
    else:
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Google did not return a refresh token. Remove this app's access at "
                    "https://myaccount.google.com/permissions and reconnect."
                ),
            )
        integration = GoogleIntegration(
            client_id=client_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.add(integration)

    await db.commit()
    return {"status": "success", "client_id": client_id}

@router.get("/locations")
async def get_google_locations(client_id: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> list[GoogleLocationOptionResponse]:
    """Fetch locations from Google Business Profile API."""
    if current_user.role != "super_admin":
        client_uuid_check = uuid.UUID(client_id)
        await verify_client_access(client_uuid_check, current_user, db)

    try:
        client = await get_client_with_agency(db, client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID")
    except LookupError:
        raise HTTPException(status_code=404, detail="Client or Agency not found")

    integration = await get_client_integration(db, client.id)
    
    if not integration:
        raise HTTPException(status_code=400, detail="Google account not connected")

    return await list_google_locations_for_client(db, client, integration)


@router.get("/status", response_model=GoogleIntegrationStatusResponse)
async def get_google_integration_status(
    client_id: str,
    location_id: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "super_admin":
        client_uuid_check = uuid.UUID(client_id)
        await verify_client_access(client_uuid_check, current_user, db)

    try:
        return await build_google_integration_status(db, client_id, location_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID")
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/map-location")
async def map_google_location(location_id: str, google_location_id: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Map a Google location ID to an internal location."""
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    location = await check_location_access(location_uuid, current_user, db)

    location.google_location_id = google_location_id
    await db.commit()
    
    return {"status": "mapped successfully"}


@router.post("/sync", response_model=GoogleSyncResponse)
async def sync_google_location_reviews(
    location_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    location = await check_location_access(location_uuid, current_user, db)

    integration = await get_client_integration(db, location.client_id)
    if not integration:
        raise HTTPException(status_code=400, detail="Google account not connected")

    try:
        client = await get_client_with_agency(db, str(location.client_id))
        return await import_google_reviews_for_location(db, location, integration, client.agency)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
