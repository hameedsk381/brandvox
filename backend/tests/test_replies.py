import pytest
from unittest.mock import AsyncMock, patch

from app.models.integration import GoogleIntegration
from app.models.review import Review, ReviewReply
from app.models.tenant import Agency, Client, Location
from app.models.user import User
from app.services.reply_service import approve_reply, save_reply

pytestmark = pytest.mark.asyncio


async def create_google_review_graph(db_session):
    agency = Agency(
        name="Agency One",
        slug="agency-one",
        google_oauth_client_id="test-client-id",
        google_oauth_client_secret="test-client-secret",
        settings={},
    )
    db_session.add(agency)
    await db_session.flush()

    client = Client(
        agency_id=agency.id,
        name="Client One",
        industry="restaurant",
        settings={},
    )
    db_session.add(client)
    await db_session.flush()

    location = Location(
        client_id=client.id,
        name="Main Branch",
        google_location_id="accounts/123/locations/456",
        timezone="UTC",
    )
    db_session.add(location)
    await db_session.flush()

    integration = GoogleIntegration(
        client_id=client.id,
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=location.created_at,
        google_account_id="accounts/123",
    )
    db_session.add(integration)

    review = Review(
        location_id=location.id,
        source="google",
        source_review_id="review-abc",
        author_name="Reviewer",
        rating=5,
        text="Great service",
        review_date=location.created_at,
    )
    db_session.add(review)

    approver = User(
        email="manager@example.com",
        hashed_password="hashed",
        name="Manager",
        role="marketing_manager",
        is_active=True,
        client_id=client.id,
        agency_id=agency.id,
    )
    db_session.add(approver)

    await db_session.commit()
    await db_session.refresh(review)
    await db_session.refresh(approver)
    return review, approver


async def test_save_reply_publishes_google_reply(db_session):
    review, approver = await create_google_review_graph(db_session)

    with patch("app.services.reply_service.publish_google_review_reply", new=AsyncMock(return_value={"comment": "Thanks"})) as mock_publish:
        reply = await save_reply(
            db=db_session,
            review_id=review.id,
            content="Thanks for your review",
            status="posted",
            generated_by="manual",
            approved_by=approver.id,
        )

    assert reply.status == "posted"
    assert mock_publish.await_count == 1


async def test_approve_reply_publishes_google_reply(db_session):
    review, approver = await create_google_review_graph(db_session)

    draft = ReviewReply(
        review_id=review.id,
        content="We appreciate your feedback",
        status="draft",
        generated_by="ai",
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)

    with patch("app.services.reply_service.publish_google_review_reply", new=AsyncMock(return_value={"comment": "OK"})) as mock_publish:
        approved = await approve_reply(db_session, draft.id, approver.id)

    assert approved is not None
    assert approved.status == "posted"
    assert approved.approved_by == approver.id
    assert mock_publish.await_count == 1
