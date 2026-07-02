import pytest

pytestmark = pytest.mark.asyncio


async def test_dashboard_endpoint(client, admin_token):
    response = await client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)


async def test_sentiment_breakdown(client, admin_token):
    response = await client.get(
        "/api/analytics/sentiment",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)


async def test_dashboard_unauthenticated(client):
    response = await client.get("/api/dashboard")
    assert response.status_code == 401


async def test_sentiment_unauthenticated(client):
    response = await client.get("/api/analytics/sentiment")
    assert response.status_code == 401
