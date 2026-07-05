"""Cross-tenant isolation regression tests.

Verifies that a user from agency B cannot read or mutate agency A's
objects via by-ID endpoints.
"""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.core.auth import create_access_token, hash_password
from app.models.review import Review
from app.models.tenant import Agency, Client, Location
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _build_agency_graph(db_session, slug: str):
    agency = Agency(name=f"Agency {slug}", slug=slug, settings={})
    db_session.add(agency)
    await db_session.flush()

    client = Client(agency_id=agency.id, name=f"Client {slug}", industry="retail", settings={})
    db_session.add(client)
    await db_session.flush()

    location = Location(client_id=client.id, name=f"Location {slug}", timezone="UTC")
    db_session.add(location)
    await db_session.flush()

    admin = User(
        email=f"admin@{slug}.test",
        hashed_password=hash_password("Password1!"),
        name=f"Admin {slug}",
        role="agency_admin",
        agency_id=agency.id,
        is_active=True,
    )
    db_session.add(admin)

    review = Review(
        location_id=location.id,
        source="manual",
        source_review_id=f"manual-{slug}-1",
        author_name="Reviewer",
        rating=2,
        text="Confidential customer complaint",
        review_date=datetime.now(timezone.utc),
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    await db_session.refresh(location)
    return agency, client, location, admin, review


@pytest_asyncio.fixture
async def two_agencies(db_session):
    a = await _build_agency_graph(db_session, "tenant-a")
    b = await _build_agency_graph(db_session, "tenant-b")
    return {"a": a, "b": b}


def _auth(user: User):
    return {"Authorization": f"Bearer {create_access_token(data={'sub': user.email})}"}


async def test_owner_can_read_own_review(client, two_agencies):
    _, _, _, admin_a, review_a = two_agencies["a"]
    response = await client.get(f"/api/reviews/{review_a.id}", headers=_auth(admin_a))
    assert response.status_code == 200
    assert response.json()["id"] == str(review_a.id)


async def test_other_agency_cannot_read_review(client, two_agencies):
    _, _, _, _, review_a = two_agencies["a"]
    _, _, _, admin_b, _ = two_agencies["b"]
    response = await client.get(f"/api/reviews/{review_a.id}", headers=_auth(admin_b))
    assert response.status_code == 403


async def test_other_agency_cannot_reply_to_review(client, two_agencies):
    _, _, _, _, review_a = two_agencies["a"]
    _, _, _, admin_b, _ = two_agencies["b"]
    response = await client.post(
        f"/api/reviews/{review_a.id}/reply",
        json={"content": "hostile takeover reply", "generated_by": "manual"},
        headers=_auth(admin_b),
    )
    assert response.status_code == 403


async def test_other_agency_cannot_read_smart_rules(client, two_agencies):
    _, _, location_a, _, _ = two_agencies["a"]
    _, _, _, admin_b, _ = two_agencies["b"]
    response = await client.get(f"/api/smart-rules/{location_a.id}", headers=_auth(admin_b))
    assert response.status_code == 403


async def test_other_agency_cannot_read_brand_voice(client, two_agencies):
    _, client_a, _, _, _ = two_agencies["a"]
    _, _, _, admin_b, _ = two_agencies["b"]
    response = await client.get(f"/api/brand-voice/{client_a.id}", headers=_auth(admin_b))
    assert response.status_code == 403


async def test_other_agency_cannot_create_location_under_foreign_client(client, two_agencies):
    _, client_a, _, _, _ = two_agencies["a"]
    _, _, _, admin_b, _ = two_agencies["b"]
    response = await client.post(
        "/api/locations",
        json={"client_id": str(client_a.id), "name": "Injected Location", "timezone": "UTC"},
        headers=_auth(admin_b),
    )
    assert response.status_code == 403
