from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import uuid

from app.models.integration import GoogleIntegration
from app.models.review import Review
from app.models.tenant import Agency, Client, Location
from app.services.google_integration_service import (
    import_google_reviews_for_location,
    mark_google_sync_status,
    _calculate_next_sync_after_failure,
)
from app.services.alert_service import notify_sync_failure
from app.models.alert import AlertIntegration, IntegrationType

pytestmark = pytest.mark.asyncio


async def create_integration_graph(db_session, *, mapped_location_id="accounts/123/locations/456"):
    agency = Agency(
        name="Test Agency",
        slug=f"test-agency-{datetime.now(timezone.utc).timestamp()}",
        google_oauth_client_id="test-client-id",
        google_oauth_client_secret="test-secret",
        settings={},
    )
    db_session.add(agency)
    await db_session.flush()

    client = Client(
        agency_id=agency.id,
        name="Test Client",
        industry="retail",
        settings={},
    )
    db_session.add(client)
    await db_session.flush()

    location = Location(
        client_id=client.id,
        name="Test Branch",
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
        sync_failures=0,
    )
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(location)
    await db_session.refresh(integration)
    return agency, client, location, integration


class TestSyncFailureBackoff:

    async def test_sync_failure_increments_failures_and_sets_next_sync(self, db_session):
        """Verify that a sync failure increments sync_failures and calculates next_sync_at."""
        agency, client, location, integration = await create_integration_graph(
            db_session, mapped_location_id="locations/456"
        )

        with pytest.raises(ValueError):
            await import_google_reviews_for_location(db_session, location, integration, agency)

        await db_session.refresh(integration)
        assert integration.sync_failures == 1
        assert integration.last_sync_status == "failed"
        assert integration.next_sync_at is not None
        assert integration.next_sync_at > datetime.now(timezone.utc)

    async def test_sync_failures_accumulate_across_multiple_failures(self, db_session):
        """Verify that repeated failures increment the counter with exponential backoff."""
        agency, client, location, integration = await create_integration_graph(
            db_session, mapped_location_id="locations/456"
        )

        for _ in range(3):
            with pytest.raises(ValueError):
                await import_google_reviews_for_location(db_session, location, integration, agency)
            await db_session.refresh(integration)

        assert integration.sync_failures == 3
        assert integration.last_sync_status == "failed"

        # 2^3 = 8 hours backoff
        expected_min = datetime.now(timezone.utc) + timedelta(hours=7)
        expected_max = datetime.now(timezone.utc) + timedelta(hours=9)
        assert expected_min < integration.next_sync_at < expected_max

    async def test_success_resets_failures_and_clears_next_sync(self, db_session):
        """Verify that a successful sync resets sync_failures to 0 and clears next_sync_at."""
        agency, client, location, integration = await create_integration_graph(db_session)

        integration.sync_failures = 3
        integration.next_sync_at = datetime.now(timezone.utc) + timedelta(hours=8)
        await db_session.commit()

        with patch(
            "app.services.google_integration_service.analyze_review_sentiment_and_topics",
            new=AsyncMock(),
        ), patch(
            "app.services.google_integration_service.check_and_apply_smart_rules",
            new=AsyncMock(),
        ), patch(
            "app.services.google_integration_service.detect_crisis",
            new=AsyncMock(),
        ):
            result = await import_google_reviews_for_location(db_session, location, integration, agency)

        assert result["status"] == "success"
        await db_session.refresh(integration)
        assert integration.sync_failures == 0
        assert integration.next_sync_at is None

    async def test_calculate_next_sync_exponential_backoff(self, db_session):
        """Verify the exponential backoff formula directly."""
        now = datetime.now(timezone.utc)

        t1 = _calculate_next_sync_after_failure(1)
        assert timedelta(hours=1.5) > (t1 - now) >= timedelta(hours=1)

        t2 = _calculate_next_sync_after_failure(2)
        assert timedelta(hours=2.5) > (t2 - now) >= timedelta(hours=2)

        t5 = _calculate_next_sync_after_failure(5)
        assert timedelta(hours=24) >= (t5 - now) >= timedelta(hours=2)

    async def test_mark_google_sync_status_failure(self, db_session):
        """Verify mark_google_sync_status increments failures on failure."""
        agency, client, location, integration = await create_integration_graph(db_session)

        await mark_google_sync_status(db_session, integration, "failed", "test error")
        assert integration.sync_failures == 1
        assert integration.last_sync_status == "failed"
        assert integration.last_sync_error == "test error"
        assert integration.next_sync_at is not None

    async def test_mark_google_sync_status_success(self, db_session):
        """Verify mark_google_sync_status resets failures on success."""
        agency, client, location, integration = await create_integration_graph(db_session)
        integration.sync_failures = 5
        integration.next_sync_at = datetime.now(timezone.utc) + timedelta(hours=24)
        await db_session.commit()

        await mark_google_sync_status(db_session, integration, "success")
        assert integration.sync_failures == 0
        assert integration.last_sync_status == "success"
        assert integration.next_sync_at is None


class TestSyncFailureNotifications:

    async def test_notify_sync_failure_dispatches_to_slack(self, db_session):
        """Verify notify_sync_failure sends a Slack webhook."""
        agency, client, location, integration = await create_integration_graph(db_session)

        alert_int = AlertIntegration(
            location_id=location.id,
            type=IntegrationType.slack,
            webhook_url="https://hooks.slack.com/test",
            is_active=True,
        )
        db_session.add(alert_int)
        await db_session.commit()

        with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
            await notify_sync_failure(db_session, location, "Test error", 2)

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "json" in call_kwargs
            assert "text" in call_kwargs["json"]
            assert "GOOGLE SYNC FAILURE" in call_kwargs["json"]["text"]
            assert "Test error" in call_kwargs["json"]["text"]

    async def test_notify_sync_failure_dispatches_to_teams(self, db_session):
        """Verify notify_sync_failure sends a Teams webhook."""
        agency, client, location, integration = await create_integration_graph(db_session)

        alert_int = AlertIntegration(
            location_id=location.id,
            type=IntegrationType.teams,
            webhook_url="https://outlook.office.com/webhook/test",
            is_active=True,
        )
        db_session.add(alert_int)
        await db_session.commit()

        with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
            await notify_sync_failure(db_session, location, "Test error", 2)

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "json" in call_kwargs
            assert call_kwargs["json"].get("@type") == "MessageCard"
            assert "GOOGLE SYNC FAILURE" in call_kwargs["json"]["summary"]

    async def test_notify_sync_failure_no_integrations(self, db_session):
        """Verify notify_sync_failure does not error when no integrations configured."""
        agency, client, location, integration = await create_integration_graph(db_session)

        with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
            await notify_sync_failure(db_session, location, "Test error", 2)
            mock_post.assert_not_called()


class TestSharedPermissions:

    async def test_verify_client_access_allows_agency_admin(self, db_session):
        """Verify an agency_admin can access their own client."""
        from app.core.dependencies import verify_client_access
        from app.models.user import User

        agency, client, location, integration = await create_integration_graph(db_session)
        user = User(
            email="agency@test.com",
            hashed_password="hash",
            name="Agency Admin",
            role="agency_admin",
            agency_id=agency.id,
            is_active=True,
        )

        result = await verify_client_access(client.id, user, db_session)
        assert result is None

    async def test_verify_client_access_denies_wrong_agency(self, db_session):
        """Verify an agency_admin cannot access a client from another agency."""
        from app.core.dependencies import verify_client_access

        from fastapi import HTTPException
        from app.models.user import User

        agency, client, location, integration = await create_integration_graph(db_session)
        user = User(
            email="other@test.com",
            hashed_password="hash",
            name="Other Admin",
            role="agency_admin",
            agency_id=uuid.uuid4(),
            is_active=True,
        )

        with pytest.raises(HTTPException) as exc:
            await verify_client_access(client.id, user, db_session)
        assert exc.value.status_code == 403


class TestSchedulerHardening:

    async def test_health_endpoint_includes_scheduler(self, db_session):
        """Verify the health endpoint returns scheduler info."""
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.database import get_db

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/health")
            data = response.json()

            assert response.status_code == 200
            assert data["status"] == "healthy"
            assert "scheduler" in data
            assert "status" in data["scheduler"]
            assert "sync_in_progress" in data["scheduler"]
            assert "jobs" in data["scheduler"]
            assert "timestamp" in data

        app.dependency_overrides.clear()
