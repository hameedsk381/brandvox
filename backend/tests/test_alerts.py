import pytest
import pytest_asyncio
from uuid import UUID
from app.models.alert import CrisisAlert, AlertIntegration, AlertSeverity, AlertCategory, AlertStatus

pytestmark = pytest.mark.asyncio

ALERTS_ENDPOINT = "/api/alerts"

@pytest_asyncio.fixture(autouse=True)
async def seed_test_data(db_session):
    from app.models.tenant import Agency, Client, Location
    from app.models.user import User
    from app.core.auth import hash_password
    from app.models.review import Review
    from datetime import datetime
    
    agency = Agency(name="Test Agency", slug="test-agency")
    db_session.add(agency)
    await db_session.commit()
    await db_session.refresh(agency)
    
    client = Client(name="Test Client", agency_id=agency.id)
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    
    location = Location(name="Test Location", client_id=client.id)
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    
    user = User(
        email="admin@reputationos.ai",
        hashed_password=hash_password("demo1234"),
        name="Admin User",
        role="super_admin",
        agency_id=agency.id,
        client_id=client.id,
        location_id=location.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    review = Review(
        location_id=location.id,
        source="manual",
        source_review_id="manual-1234",
        author_name="Angry Customer",
        rating=1,
        text="I got food poisoning and I will sue this place!",
        review_date=datetime.utcnow()
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    
    # Run alert detection on the review
    from app.services.alert_service import detect_crisis
    await detect_crisis(db_session, review.id)
    
    return {
        "agency_id": agency.id,
        "client_id": client.id,
        "location_id": location.id,
        "review_id": review.id
    }

async def test_list_alerts_unauthenticated(client, seed_test_data):
    loc_id = seed_test_data["location_id"]
    response = await client.get(f"{ALERTS_ENDPOINT}?location_id={loc_id}")
    assert response.status_code == 401

async def test_alerts_flow(client, admin_token, seed_test_data):
    loc_id = seed_test_data["location_id"]
    
    # 1. Check Integrations
    response = await client.get(
        f"{ALERTS_ENDPOINT}/integrations?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # 2. Add Integration
    response = await client.post(
        f"{ALERTS_ENDPOINT}/integrations?location_id={loc_id}",
        json={"type": "slack", "webhook_url": "https://hooks.slack.com/services/test/test/test", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    integration = response.json()
    assert integration["type"] == "slack"
    
    # 3. List Alerts
    # The detect_crisis method should have added an alert due to "food poisoning" and "sue" keywords.
    response = await client.get(
        f"{ALERTS_ENDPOINT}?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    alert = alerts[0]
    assert alert["status"] == "open"
    assert "review_text" in alert
    alert_id = alert["id"]
    
    # 4. Resolve Alert
    response = await client.patch(
        f"{ALERTS_ENDPOINT}/{alert_id}/resolve?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    resolved = response.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None
