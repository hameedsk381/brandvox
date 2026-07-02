import pytest
import pytest_asyncio
from uuid import UUID
from app.models.competitor import Competitor

pytestmark = pytest.mark.asyncio

COMPETITORS_ENDPOINT = "/api/competitors"

@pytest_asyncio.fixture(autouse=True)
async def seed_test_data(db_session):
    from app.models.tenant import Agency, Client, Location
    from app.models.user import User
    from app.core.auth import hash_password
    
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
    
    return {
        "agency_id": agency.id,
        "client_id": client.id,
        "location_id": location.id
    }

async def test_list_competitors_unauthenticated(client, seed_test_data):
    loc_id = seed_test_data["location_id"]
    response = await client.get(f"{COMPETITORS_ENDPOINT}?location_id={loc_id}")
    assert response.status_code == 401

async def test_competitors_flow(client, admin_token, seed_test_data):
    loc_id = seed_test_data["location_id"]
    
    # 1. Add Competitor
    response = await client.post(
        f"{COMPETITORS_ENDPOINT}?location_id={loc_id}",
        json={"name": "Competitor Pizza"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    comp = response.json()
    assert comp["name"] == "Competitor Pizza"
    comp_id = comp["id"]
    
    # 2. List Competitors
    response = await client.get(
        f"{COMPETITORS_ENDPOINT}?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    competitors = response.json()
    assert len(competitors) == 1
    assert competitors[0]["name"] == "Competitor Pizza"
    
    # 3. Get Analytics
    response = await client.get(
        f"{COMPETITORS_ENDPOINT}/analytics?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    analytics = response.json()
    assert "client" in analytics
    assert "competitors" in analytics
    assert len(analytics["competitors"]) == 1
    assert analytics["competitors"][0]["name"] == "Competitor Pizza"
    assert analytics["competitors"][0]["review_count"] == 10 # Seeder adds 10 reviews
    
    # 4. Trigger AI Analysis
    response = await client.post(
        f"{COMPETITORS_ENDPOINT}/analyze?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    analysis = response.json()
    assert "strengths" in analysis
    assert "weaknesses" in analysis
    assert "opportunities" in analysis
    
    # 5. Get latest AI Analysis
    response = await client.get(
        f"{COMPETITORS_ENDPOINT}/analysis?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    latest = response.json()
    assert latest["summary"] == analysis["summary"]
    
    # 6. Delete Competitor
    response = await client.delete(
        f"{COMPETITORS_ENDPOINT}/{comp_id}?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 7. List Competitors should be empty
    response = await client.get(
        f"{COMPETITORS_ENDPOINT}?location_id={loc_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 0
