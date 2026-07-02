from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.integration import GoogleIntegration
from app.models.review import Review
from app.models.tenant import Agency, Client, Location
from app.services.google_integration_service import import_google_reviews_for_location, publish_google_review_reply

pytestmark = pytest.mark.asyncio


async def create_integration_graph(db_session, *, mapped_location_id: str | None = "accounts/123/locations/456"):
    agency = Agency(
        name="Agency Obs",
        slug=f"agency-obs-{datetime.now(timezone.utc).timestamp()}",
        google_oauth_client_id="real-client-id",
        google_oauth_client_secret="real-secret",
        settings={},
    )
    db_session.add(agency)
    await db_session.flush()

    client = Client(
        agency_id=agency.id,
        name="Client Obs",
        industry="retail",
        settings={},
    )
    db_session.add(client)
    await db_session.flush()

    location = Location(
        client_id=client.id,
        name="Obs Branch",
        google_location_id=mapped_location_id,
        timezone="UTC",
    )
    db_session.add(location)
    await db_session.flush()

    integration = GoogleIntegration(
        client_id=client.id,
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        google_account_id="accounts/123",
    )
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(location)
    await db_session.refresh(integration)
    return agency, client, location, integration


async def test_sync_failure_marks_integration_status(db_session):
    agency, client, location, integration = await create_integration_graph(db_session, mapped_location_id="locations/456")

    with pytest.raises(ValueError):
        await import_google_reviews_for_location(db_session, location, integration, agency)

    await db_session.refresh(integration)
    assert integration.last_sync_status == "failed"
    assert integration.last_sync_error is not None
    assert "Re-map the location" in integration.last_sync_error
    assert integration.last_sync_attempt_at is not None
    assert integration.sync_failures == 1
    assert integration.next_sync_at is not None


async def test_reply_failure_marks_integration_status(db_session):
    agency, client, location, integration = await create_integration_graph(db_session)
    review = Review(
        location_id=location.id,
        source="google",
        source_review_id="review-123",
        author_name="Test Reviewer",
        rating=5,
        text="Great service",
        review_date=datetime.now(timezone.utc),
    )
    db_session.add(review)
    await db_session.commit()

    with patch("app.services.google_integration_service.ensure_valid_google_access_token", new=AsyncMock(return_value=integration)):
        with patch("app.services.google_integration_service._google_put", new=AsyncMock(side_effect=ValueError("Google publish failed"))):
            with pytest.raises(ValueError):
                await publish_google_review_reply(
                    db_session,
                    agency,
                    integration,
                    location,
                    "review-123",
                    "Thank you for your feedback",
                )

    await db_session.refresh(integration)
    assert integration.last_reply_status == "failed"
    assert integration.last_reply_error == "Google publish failed"
    assert integration.last_reply_attempt_at is not None
