import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.core.auth import create_access_token, hash_password
from app.main import app
from app.models.tenant import Agency, Client, Location
from app.models.integration import GoogleIntegration
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _seed_test_data(db_session):
    agency = Agency(
        name="E2E Agency",
        slug=f"e2e-{datetime.utcnow().timestamp()}",
        google_oauth_client_id="test-client-id",
        google_oauth_client_secret="test-secret",
        settings={},
    )
    db_session.add(agency)
    await db_session.flush()

    client = Client(
        agency_id=agency.id,
        name="E2E Client",
        industry="retail",
        settings={},
    )
    db_session.add(client)
    await db_session.flush()

    location = Location(
        client_id=client.id,
        name="E2E Branch",
        timezone="UTC",
    )
    db_session.add(location)
    await db_session.flush()

    user = User(
        email="e2e@test.com",
        hashed_password=hash_password("testpass123"),
        name="E2E User",
        role="super_admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(agency)
    await db_session.refresh(client)
    await db_session.refresh(location)
    await db_session.refresh(user)
    return agency, client, location, user


@pytest.mark.parametrize("use_auth", [True, False])
async def test_1_auth_url_endpoint(db_session, use_auth):
    """GET /api/integrations/google/auth-url"""
    agency, client, location, user = await _seed_test_data(db_session)

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    headers = {}
    if use_auth:
        token = create_access_token(data={"sub": user.email})
        headers["Authorization"] = f"Bearer {token}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/integrations/google/auth-url?client_id={client.id}",
            headers=headers,
        )

    app.dependency_overrides.clear()

    if use_auth:
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "url" in data
        assert "accounts.google.com" in data["url"]
        assert str(client.id) in data["url"]
    else:
        assert resp.status_code == 401


async def test_2_status_before_connect(db_session):
    """GET /api/integrations/google/status before OAuth"""
    agency, client, location, user = await _seed_test_data(db_session)
    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}&location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["is_configured"] is True
    assert data["is_connected"] is False
    assert data["client_id"] == str(client.id)


async def test_3_oauth_callback(db_session):
    """POST /api/integrations/google/callback"""
    agency, client, location, user = await _seed_test_data(db_session)
    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/integrations/google/callback?code=test-code&state={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json()["status"] == "success"


async def test_4_status_after_connect(db_session):
    """GET /api/integrations/google/status after OAuth"""
    agency, client, location, user = await _seed_test_data(db_session)
    integration = GoogleIntegration(
        client_id=client.id,
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        google_account_id="accounts/test",
    )
    db_session.add(integration)
    await db_session.commit()

    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}&location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["is_connected"] is True
    assert data["google_account_id"] == "accounts/test"
    assert len(data["available_locations"]) > 0


async def test_5_fetch_locations(db_session):
    """GET /api/integrations/google/locations"""
    agency, client, location, user = await _seed_test_data(db_session)
    integration = GoogleIntegration(
        client_id=client.id,
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        google_account_id="accounts/test",
    )
    db_session.add(integration)
    await db_session.commit()

    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/integrations/google/locations?client_id={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert len(data) > 0
    for loc in data:
        assert "name" in loc
        assert "title" in loc


async def test_6_map_location(db_session):
    """POST /api/integrations/google/map-location"""
    agency, client, location, user = await _seed_test_data(db_session)
    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    google_location_id = "accounts/mock-account/locations/mock-primary"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/integrations/google/map-location?location_id={location.id}&google_location_id={google_location_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json()["status"] == "mapped successfully"

    await db_session.refresh(location)
    assert location.google_location_id == google_location_id


async def test_7_sync_reviews_mock(db_session):
    """POST /api/integrations/google/sync - uses mock reviews fallback"""
    agency, client, location, user = await _seed_test_data(db_session)
    location.google_location_id = "accounts/123/locations/456"
    await db_session.commit()

    integration = GoogleIntegration(
        client_id=client.id,
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        google_account_id="accounts/test",
    )
    db_session.add(integration)
    await db_session.commit()

    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/integrations/google/sync?location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert data["imported_reviews"] >= 0
    assert data["synced_location_id"] == str(location.id)


async def test_8_status_after_sync(db_session):
    """Verify status reflects sync activity"""
    agency, client, location, user = await _seed_test_data(db_session)
    location.google_location_id = "accounts/123/locations/456"
    await db_session.commit()

    integration = GoogleIntegration(
        client_id=client.id,
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        google_account_id="accounts/test",
        last_sync_status="success",
        last_sync_attempt_at=datetime.utcnow(),
        sync_failures=0,
    )
    db_session.add(integration)
    await db_session.commit()

    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}&location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["is_connected"] is True
    assert data["mapped_google_location_id"] == location.google_location_id
    assert data["last_sync_status"] == "success"
    assert data["sync_failures"] == 0


async def test_9_full_e2e_flow(db_session):
    """Complete end-to-end: connect -> status -> locations -> map -> sync -> status"""
    from app.services.google_integration_service import import_google_reviews_for_location

    agency, client, location, user = await _seed_test_data(db_session)
    token = create_access_token(data={"sub": user.email})

    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Step 1: Status before connect
        r1 = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        assert r1.json()["is_connected"] is False

        # Step 2: Connect (OAuth callback with test client)
        r2 = await ac.post(
            f"/api/integrations/google/callback?code=test&state={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200

        # Step 3: Status after connect
        r3 = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 200
        assert r3.json()["is_connected"] is True
        assert len(r3.json()["available_locations"]) > 0

        # Step 4: Fetch locations
        r4 = await ac.get(
            f"/api/integrations/google/locations?client_id={client.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r4.status_code == 200
        locations = r4.json()
        assert len(locations) > 0

        # Step 5: Map location
        google_loc = locations[0]["name"]
        r5 = await ac.post(
            f"/api/integrations/google/map-location?location_id={location.id}&google_location_id={google_loc}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r5.status_code == 200

        # Step 6: Sync reviews
        r6 = await ac.post(
            f"/api/integrations/google/sync?location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r6.status_code == 200, f"Sync failed: {r6.text}"
        sync_data = r6.json()
        assert sync_data["status"] == "success"
        assert sync_data["imported_reviews"] > 0

        # Step 7: Status after sync
        r7 = await ac.get(
            f"/api/integrations/google/status?client_id={client.id}&location_id={location.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r7.status_code == 200
        status = r7.json()
        assert status["is_connected"] is True
        assert status["mapped_google_location_id"] is not None
        assert status["last_sync_status"] in ("success", None)

    app.dependency_overrides.clear()
