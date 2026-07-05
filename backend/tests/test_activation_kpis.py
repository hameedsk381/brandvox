"""Activation KPI tests (roadmap Phase 6 scoreboard).

Covers the /api/analytics/activation endpoint and the stamp-once semantics
of Agency.first_synced_at / first_ai_reply_at.
"""
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import update

from app.core.auth import create_access_token, hash_password
from app.models.tenant import Agency, Client, Location
from app.models.user import User

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def agency_graph(db_session):
    agency = Agency(name="Activation Agency", slug="activation-agency", settings={})
    db_session.add(agency)
    await db_session.flush()

    client_row = Client(agency_id=agency.id, name="Activation Client", industry="Restaurant", settings={})
    db_session.add(client_row)
    await db_session.flush()

    location = Location(client_id=client_row.id, name="Activation Location", timezone="UTC")
    db_session.add(location)

    admin = User(
        email="admin@activation.test",
        hashed_password=hash_password("Password1!"),
        name="Activation Admin",
        role="agency_admin",
        agency_id=agency.id,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(agency)
    return agency, client_row, location, admin


def _auth(user: User):
    return {"Authorization": f"Bearer {create_access_token(data={'sub': user.email})}"}


async def test_activation_empty_before_any_sync(client, agency_graph):
    agency, _, _, admin = agency_graph
    response = await client.get("/api/analytics/activation", headers=_auth(admin))
    assert response.status_code == 200
    body = response.json()
    assert body["agency_id"] == str(agency.id)
    assert body["first_synced_at"] is None
    assert body["first_ai_reply_at"] is None
    assert body["seconds_to_first_sync"] is None
    assert body["seconds_to_first_ai_reply"] is None


async def test_activation_deltas_computed(client, db_session, agency_graph):
    agency, _, _, admin = agency_graph
    first_sync = agency.created_at + timedelta(minutes=10)
    first_reply = agency.created_at + timedelta(minutes=25)
    agency.first_synced_at = first_sync
    agency.first_ai_reply_at = first_reply
    await db_session.commit()

    response = await client.get("/api/analytics/activation", headers=_auth(admin))
    assert response.status_code == 200
    body = response.json()
    assert body["seconds_to_first_sync"] == pytest.approx(600, abs=1)
    assert body["seconds_to_first_ai_reply"] == pytest.approx(1500, abs=1)


async def test_stamp_is_write_once(db_session, agency_graph):
    """The guarded UPDATE used by sync/reply must not overwrite an existing stamp."""
    agency, _, _, _ = agency_graph
    original = datetime(2026, 1, 1, 12, 0, 0)
    agency.first_synced_at = original
    await db_session.commit()

    await db_session.execute(
        update(Agency)
        .where(Agency.id == agency.id, Agency.first_synced_at.is_(None))
        .values(first_synced_at=datetime.utcnow())
    )
    await db_session.commit()
    await db_session.refresh(agency)
    assert agency.first_synced_at == original


async def test_non_super_admin_cannot_query_other_agency(client, db_session, agency_graph):
    _, _, _, admin = agency_graph
    other = Agency(name="Other Agency", slug="other-agency", settings={})
    db_session.add(other)
    await db_session.commit()

    response = await client.get(
        f"/api/analytics/activation?agency_id={other.id}", headers=_auth(admin)
    )
    assert response.status_code == 403
