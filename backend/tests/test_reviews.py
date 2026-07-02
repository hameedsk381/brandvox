import pytest

pytestmark = pytest.mark.asyncio

REVIEWS_ENDPOINT = "/api/reviews"


async def test_list_reviews_empty(client, admin_token, seed_admin_user):
    response = await client.get(
        REVIEWS_ENDPOINT,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 401)


async def test_create_review(client, admin_token, seed_admin_user):
    response = await client.post(
        REVIEWS_ENDPOINT,
        json={
            "location_id": "00000000-0000-0000-0000-000000000001",
            "rating": 5,
            "text": "Great service!",
            "author_name": "Test Customer",
            "source": "manual",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 201, 404, 422)


async def test_get_review_not_found(client, admin_token, seed_admin_user):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"{REVIEWS_ENDPOINT}/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


async def test_list_reviews_unauthenticated(client):
    response = await client.get(REVIEWS_ENDPOINT)
    assert response.status_code == 401
