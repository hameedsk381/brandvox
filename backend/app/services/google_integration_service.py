import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.integration import GoogleIntegration
from app.models.review import Review
from app.models.tenant import Agency, Client, Location

logger = logging.getLogger(__name__)

GOOGLE_ACCOUNT_MANAGEMENT_BASE_URL = "https://mybusinessaccountmanagement.googleapis.com/v1.1"
GOOGLE_BUSINESS_INFORMATION_BASE_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"
GOOGLE_REVIEWS_BASE_URL = "https://mybusiness.googleapis.com/v4"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKEN_REFRESH_BUFFER_MINUTES = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def mark_google_sync_status(
    db: AsyncSession,
    integration: GoogleIntegration,
    status: str,
    error: Optional[str] = None,
) -> None:
    integration.last_sync_status = status
    integration.last_sync_error = error
    integration.last_sync_attempt_at = _utcnow()
    await db.commit()
    await db.refresh(integration)


async def mark_google_reply_status(
    db: AsyncSession,
    integration: GoogleIntegration,
    status: str,
    error: Optional[str] = None,
) -> None:
    integration.last_reply_status = status
    integration.last_reply_error = error
    integration.last_reply_attempt_at = _utcnow()
    await db.commit()
    await db.refresh(integration)


def _build_mock_locations(client: Client) -> List[Dict[str, str]]:
    base_name = client.name or "Business"
    return [
        {"name": "accounts/mock-account/locations/mock-primary", "title": f"{base_name} Main Location"},
        {"name": "accounts/mock-account/locations/mock-secondary", "title": f"{base_name} Downtown Location"},
    ]


def _build_mock_reviews(location: Location) -> List[Dict[str, Any]]:
    seed = str(location.id).replace("-", "")[:8]
    now = datetime.now(timezone.utc)
    return [
        {
            "review_id": f"google-{seed}-1",
            "author_name": "Ava Brooks",
            "rating": 5,
            "comment": f"Great experience at {location.name}. Staff was quick and friendly.",
            "create_time": now.isoformat(),
        },
        {
            "review_id": f"google-{seed}-2",
            "author_name": "Mason Lee",
            "rating": 3,
            "comment": f"Service at {location.name} was fine, but wait time needs improvement.",
            "create_time": now.isoformat(),
        },
        {
            "review_id": f"google-{seed}-3",
            "author_name": "Sophia Patel",
            "rating": 1,
            "comment": f"Billing issue at {location.name}. Needs follow-up from the team.",
            "create_time": now.isoformat(),
        },
    ]


async def get_client_with_agency(db: AsyncSession, client_id: str) -> Client:
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError as exc:
        raise ValueError("Invalid client ID") from exc

    result = await db.execute(
        select(Client).filter(Client.id == client_uuid).options(selectinload(Client.agency))
    )
    client = result.scalars().first()
    if not client or not client.agency:
        raise LookupError("Client or Agency not found")
    return client


async def get_client_integration(db: AsyncSession, client_id: uuid.UUID) -> Optional[GoogleIntegration]:
    result = await db.execute(select(GoogleIntegration).filter(GoogleIntegration.client_id == client_id))
    return result.scalars().first()


def _is_test_mode(agency: Agency) -> bool:
    return agency.google_oauth_client_id == "test-client-id"


def _token_needs_refresh(integration: GoogleIntegration) -> bool:
    if not integration.expires_at:
        return True

    expires_at = integration.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at <= _utcnow() + timedelta(minutes=TOKEN_REFRESH_BUFFER_MINUTES)


async def refresh_google_access_token(
    db: AsyncSession, agency: Agency, integration: GoogleIntegration
) -> GoogleIntegration:
    if _is_test_mode(agency):
        integration.expires_at = _utcnow() + timedelta(hours=1)
        await db.commit()
        await db.refresh(integration)
        return integration

    if not integration.refresh_token:
        raise ValueError("Google integration is missing a refresh token")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": agency.google_oauth_client_id,
                "client_secret": agency.google_oauth_client_secret,
                "refresh_token": integration.refresh_token,
                "grant_type": "refresh_token",
            },
        )

    if response.status_code != 200:
        logger.error("Google token refresh failed: %s %s", response.status_code, response.text)
        raise ValueError("Failed to refresh Google access token")

    token_data = response.json()
    integration.access_token = token_data["access_token"]
    integration.expires_at = _utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
    await db.commit()
    await db.refresh(integration)
    return integration


async def ensure_valid_google_access_token(
    db: AsyncSession, agency: Agency, integration: GoogleIntegration
) -> GoogleIntegration:
    if _is_test_mode(agency):
        return integration

    if _token_needs_refresh(integration):
        return await refresh_google_access_token(db, agency, integration)

    return integration


async def _google_get(
    url: str, access_token: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        logger.error("Google API request failed: %s %s", response.status_code, response.text)
        raise ValueError("Failed to fetch data from Google Business Profile")

    return response.json()


async def _google_put(
    url: str, access_token: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.put(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        logger.error("Google API PUT failed: %s %s", response.status_code, response.text)
        raise ValueError("Failed to publish reply to Google Business Profile")

    return response.json()


async def fetch_google_accounts(agency: Agency, integration: GoogleIntegration) -> List[Dict[str, Any]]:
    if _is_test_mode(agency):
        return [{"name": "accounts/mock-account", "accountName": "Mock Account"}]

    accounts: List[Dict[str, Any]] = []
    next_page_token: Optional[str] = None

    while True:
        params: Dict[str, Any] = {}
        if next_page_token:
            params["pageToken"] = next_page_token

        payload = await _google_get(
            f"{GOOGLE_ACCOUNT_MANAGEMENT_BASE_URL}/accounts",
            integration.access_token,
            params=params,
        )
        accounts.extend(payload.get("accounts", []))
        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return accounts


async def fetch_google_locations(
    agency: Agency, integration: GoogleIntegration, account_name: str
) -> List[Dict[str, Any]]:
    if _is_test_mode(agency):
        return [
            {"name": "locations/mock-primary", "title": "Mock Main Location"},
            {"name": "locations/mock-secondary", "title": "Mock Downtown Location"},
        ]

    locations: List[Dict[str, Any]] = []
    next_page_token: Optional[str] = None

    while True:
        params: Dict[str, Any] = {
            "readMask": "name,title",
            "pageSize": 100,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        payload = await _google_get(
            f"{GOOGLE_BUSINESS_INFORMATION_BASE_URL}/{account_name}/locations",
            integration.access_token,
            params=params,
        )
        locations.extend(payload.get("locations", []))
        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return locations


async def list_google_locations_for_client(
    db: AsyncSession, client: Client, integration: GoogleIntegration
) -> List[Dict[str, str]]:
    agency: Agency = client.agency
    if _is_test_mode(agency):
        return _build_mock_locations(client)

    integration = await ensure_valid_google_access_token(db, agency, integration)
    accounts = await fetch_google_accounts(agency, integration)

    location_options: List[Dict[str, str]] = []
    primary_account_name: Optional[str] = None

    for account in accounts:
        account_name = account.get("name")
        if not account_name:
            continue
        if primary_account_name is None:
            primary_account_name = account_name

        locations = await fetch_google_locations(agency, integration, account_name)
        for location in locations:
            location_name = location.get("name")
            if not location_name:
                continue
            location_options.append(
                {
                    "name": f"{account_name}/{location_name}" if not location_name.startswith("accounts/") else location_name,
                    "title": location.get("title") or location_name.split("/")[-1],
                }
            )

    if primary_account_name and integration.google_account_id != primary_account_name:
        integration.google_account_id = primary_account_name
        await db.commit()

    return location_options


def _normalize_google_review_parent(google_location_id: str) -> str:
    if google_location_id.startswith("accounts/"):
        return google_location_id
    if google_location_id.startswith("locations/"):
        raise ValueError("Google location mapping is incomplete. Re-map the location from the integrations page.")
    raise ValueError("Invalid Google location mapping")


def _parse_google_star_rating(value: Optional[str]) -> int:
    star_map = {
        "ONE": 1,
        "TWO": 2,
        "THREE": 3,
        "FOUR": 4,
        "FIVE": 5,
    }
    return star_map.get(value or "", 5)


async def fetch_google_reviews_for_parent(
    agency: Agency, integration: GoogleIntegration, review_parent: str
) -> List[Dict[str, Any]]:
    if _is_test_mode(agency):
        raise ValueError("Mock review fetch should be handled before live Google review fetch")

    reviews: List[Dict[str, Any]] = []
    next_page_token: Optional[str] = None

    while True:
        params: Dict[str, Any] = {
            "pageSize": 50,
            "orderBy": "updateTime desc",
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        payload = await _google_get(
            f"{GOOGLE_REVIEWS_BASE_URL}/{review_parent}/reviews",
            integration.access_token,
            params=params,
        )
        reviews.extend(payload.get("reviews", []))
        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break

    return reviews


def build_google_review_name(location: Location, source_review_id: str) -> str:
    if not location.google_location_id:
        raise ValueError("Location is not mapped to a Google Business Profile location")

    review_parent = _normalize_google_review_parent(location.google_location_id)
    return f"{review_parent}/reviews/{source_review_id}"


async def publish_google_review_reply(
    db: AsyncSession,
    agency: Agency,
    integration: GoogleIntegration,
    location: Location,
    source_review_id: str,
    content: str,
) -> Dict[str, Any]:
    if _is_test_mode(agency):
        logger.info("MOCK PUBLISH reply to GBP for location %s: %s", location.google_location_id, content)
        await mark_google_reply_status(db, integration, "success", None)
        return {"comment": content}

    try:
        integration = await ensure_valid_google_access_token(db, agency, integration)
        review_name = build_google_review_name(location, source_review_id)
        result = await _google_put(
            f"{GOOGLE_REVIEWS_BASE_URL}/{review_name}/reply",
            integration.access_token,
            {"comment": content},
        )
    except ValueError as exc:
        await mark_google_reply_status(db, integration, "failed", str(exc))
        raise

    await mark_google_reply_status(db, integration, "success", None)
    return result


async def build_google_integration_status(
    db: AsyncSession, client_id: str, location_id: Optional[str] = None
) -> Dict[str, Any]:
    client = await get_client_with_agency(db, client_id)
    integration = await get_client_integration(db, client.id)

    location: Optional[Location] = None
    if location_id:
        result = await db.execute(select(Location).filter(Location.id == location_id, Location.client_id == client.id))
        location = result.scalars().first()
        if not location:
            raise LookupError("Location not found for client")

    is_configured = bool(client.agency.google_oauth_client_id and client.agency.google_oauth_client_secret)
    is_connected = integration is not None
    available_locations: List[Dict[str, str]] = []

    if is_connected:
        available_locations = await list_google_locations_for_client(db, client, integration)

    return {
        "is_configured": is_configured,
        "is_connected": is_connected,
        "client_id": client_id,
        "google_account_id": integration.google_account_id if integration else None,
        "token_expires_at": integration.expires_at if integration else None,
        "last_sync_status": integration.last_sync_status if integration else None,
        "last_sync_error": integration.last_sync_error if integration else None,
        "last_sync_attempt_at": integration.last_sync_attempt_at if integration else None,
        "last_reply_status": integration.last_reply_status if integration else None,
        "last_reply_error": integration.last_reply_error if integration else None,
        "last_reply_attempt_at": integration.last_reply_attempt_at if integration else None,
        "mapped_location_id": str(location.id) if location and location.google_location_id else None,
        "mapped_google_location_id": location.google_location_id if location else None,
        "last_sync_time": location.last_sync_time if location else None,
        "available_locations": available_locations,
    }


async def import_google_reviews_for_location(
    db: AsyncSession, location: Location, integration: GoogleIntegration, agency: Agency
) -> Dict[str, Any]:
    from app.services.alert_service import detect_crisis
    from app.services.reply_service import check_and_apply_smart_rules
    from app.services.sentiment_service import analyze_review_sentiment_and_topics

    try:
        if not location.google_location_id:
            raise ValueError("Location is not mapped to a Google Business Profile location")

        if _is_test_mode(agency) or not integration.access_token:
            external_reviews = _build_mock_reviews(location)
        else:
            integration = await ensure_valid_google_access_token(db, agency, integration)
            review_parent = _normalize_google_review_parent(location.google_location_id)
            external_reviews = await fetch_google_reviews_for_parent(agency, integration, review_parent)

        imported = 0
        skipped = 0
        imported_review_ids: List[uuid.UUID] = []

        for item in external_reviews:
            source_review_id = item.get("review_id") or item.get("reviewId")
            if not source_review_id:
                logger.warning("Skipping Google review without reviewId for location %s", location.id)
                skipped += 1
                continue

            existing = await db.execute(
                select(Review).filter(Review.source == "google", Review.source_review_id == source_review_id)
            )
            if existing.scalars().first():
                skipped += 1
                continue

            reviewer = item.get("reviewer", {})
            review_date_raw = item.get("create_time") or item.get("createTime")
            try:
                review_date = datetime.fromisoformat(review_date_raw.replace("Z", "+00:00")) if review_date_raw else _utcnow()
            except ValueError:
                review_date = _utcnow()

            review = Review(
                    location_id=location.id,
                    source="google",
                    source_review_id=source_review_id,
                    author_name=item.get("author_name") or reviewer.get("displayName"),
                    author_image_url=item.get("author_image_url") or reviewer.get("profilePhotoUrl"),
                    rating=int(item.get("rating", _parse_google_star_rating(item.get("starRating")))),
                    text=item.get("comment"),
                    review_date=review_date,
            )
            db.add(review)
            await db.flush()
            imported_review_ids.append(review.id)
            imported += 1

        location.last_sync_time = _utcnow()
        await db.commit()
        await db.refresh(location)

        for review_id in imported_review_ids:
            await analyze_review_sentiment_and_topics(db, review_id)
            await check_and_apply_smart_rules(db, review_id)
            await detect_crisis(db, review_id)

        await mark_google_sync_status(db, integration, "success", None)
        return {
            "status": "success",
            "imported_reviews": imported,
            "skipped_reviews": skipped,
            "synced_location_id": str(location.id),
            "google_location_id": location.google_location_id,
            "last_sync_time": location.last_sync_time,
        }
    except ValueError as exc:
        await mark_google_sync_status(db, integration, "failed", str(exc))
        raise
