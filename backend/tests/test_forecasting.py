import pytest
from datetime import datetime, timedelta
from app.models.tenant import Agency, Client, Location
from app.models.review import Review

pytestmark = pytest.mark.asyncio

async def test_forecasting_endpoint(client, admin_token, seed_admin_user, db_session):
    # 1. Create Tenant structure
    agency = Agency(name="Test Agency", slug="test-agency")
    db_session.add(agency)
    await db_session.commit()
    await db_session.refresh(agency)
    
    tenant_client = Client(name="Test Client", agency_id=agency.id)
    db_session.add(tenant_client)
    await db_session.commit()
    await db_session.refresh(tenant_client)
    
    location = Location(name="Test Location", client_id=tenant_client.id)
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    
    # 2. Add some mock reviews for historical dataset
    for i in range(5):
        review = Review(
            location_id=location.id,
            source="manual",
            source_review_id=f"manual-rev-{i}",
            author_name=f"Customer {i}",
            rating=4 + (i % 2), # 4 or 5 stars
            text="Decent service, would come back again.",
            review_date=datetime.utcnow() - timedelta(days=i * 5)
        )
        db_session.add(review)
    await db_session.commit()
    
    # 3. Hit the forecasting endpoint
    response = await client.get(
        f"/api/forecasting?location_id={location.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "predicted_rating" in data
    assert "predicted_volume" in data
    assert "churn_risk_score" in data
    assert "reputation_risks" in data
    assert "seasonal_trends" in data
    assert "actionable_advice" in data
    assert "historical_data" in data
    assert len(data["historical_data"]) > 0
    
async def test_forecasting_location_not_found(client, admin_token, seed_admin_user):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/forecasting?location_id={fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
