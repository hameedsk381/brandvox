"""Regression tests for the July 2026 workflow review fixes:

1. Smart-rule default must never auto-publish (no rule => drafts, not auto_reply)
2. First-sync backfill must not run smart rules / crisis detection on
   reviews older than the Google connection
3. Webhook retries must update the original delivery row, not create new ones
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.review import Review, ReviewReply
from app.models.tenant import Agency, Client, Location
from app.models.integration import GoogleIntegration
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.services.reply_service import check_and_apply_smart_rules
from app.services.google_integration_service import import_google_reviews_for_location
from app.services.webhook_service import MAX_RETRIES, _next_retry_at, _record_delivery

pytestmark = pytest.mark.asyncio


async def _graph(db):
    agency = Agency(name="WF Agency", slug="wf-agency", settings={})
    db.add(agency)
    await db.flush()
    client = Client(agency_id=agency.id, name="WF Client", industry="Restaurant", settings={})
    db.add(client)
    await db.flush()
    location = Location(client_id=client.id, name="WF Location", timezone="UTC")
    db.add(location)
    await db.flush()
    integration = GoogleIntegration(
        client_id=client.id,
        access_token="tok",
        refresh_token="ref",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(integration)
    await db.commit()
    return agency, client, location, integration


async def _add_review(db, location, rating):
    review = Review(
        location_id=location.id,
        source="manual",
        source_review_id=f"wf-{rating}-{datetime.utcnow().timestamp()}",
        author_name="Reviewer",
        rating=rating,
        text="some text",
        review_date=datetime.now(timezone.utc),
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


FAKE_OPTIONS = [{"content": "Thank you!"}, {"content": "Thanks a lot!"}]


class TestSmartRuleSafeDefault:
    async def test_five_star_without_rule_drafts_instead_of_publishing(self, db_session):
        _, _, location, _ = await _graph(db_session)
        review = await _add_review(db_session, location, rating=5)

        with patch("app.services.reply_service.generate_reply", new=AsyncMock(return_value=FAKE_OPTIONS)):
            outcome = await check_and_apply_smart_rules(db_session, review.id)

        assert outcome == "draft"
        replies = (await db_session.execute(
            select(ReviewReply).filter(ReviewReply.review_id == review.id)
        )).scalars().all()
        assert replies, "expected AI drafts to be saved"
        assert all(r.status == "draft" for r in replies), "no reply may be auto-posted without an explicit rule"

    async def test_one_star_without_rule_never_publishes(self, db_session):
        _, _, location, _ = await _graph(db_session)
        review = await _add_review(db_session, location, rating=1)

        with patch("app.services.reply_service.generate_reply", new=AsyncMock(return_value=FAKE_OPTIONS)):
            outcome = await check_and_apply_smart_rules(db_session, review.id)

        assert outcome == "draft"
        replies = (await db_session.execute(
            select(ReviewReply).filter(ReviewReply.review_id == review.id)
        )).scalars().all()
        assert all(r.status == "draft" for r in replies)


class TestBackfillGuard:
    async def test_first_sync_backlog_skips_smart_rules_and_crisis(self, db_session):
        agency, _, location, integration = await _graph(db_session)
        agency.google_oauth_client_id = "real-client-id"
        location.google_location_id = "accounts/1/locations/2"
        await db_session.commit()

        old = (integration.created_at - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent = (datetime.utcnow() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        items = [
            {"reviewId": "bf-old", "starRating": "FIVE", "comment": "old praise",
             "createTime": old, "reviewer": {"displayName": "Old Reviewer"}},
            {"reviewId": "bf-new", "starRating": "FIVE", "comment": "new praise",
             "createTime": recent, "reviewer": {"displayName": "New Reviewer"}},
        ]

        smart_rules_mock = AsyncMock()
        crisis_mock = AsyncMock()
        with patch("app.services.sentiment_service.analyze_review_sentiment_and_topics", new=AsyncMock()), \
             patch("app.services.reply_service.check_and_apply_smart_rules", new=smart_rules_mock), \
             patch("app.services.alert_service.detect_crisis", new=crisis_mock), \
             patch("app.services.google_integration_service.ensure_valid_google_access_token",
                   new=AsyncMock(return_value=integration)), \
             patch("app.services.google_integration_service.fetch_google_reviews_for_parent",
                   new=AsyncMock(return_value=items)):
            result = await import_google_reviews_for_location(db_session, location, integration, agency)

        assert result["imported_reviews"] == 2
        # Only the post-connection review may trigger automation
        assert smart_rules_mock.await_count == 1
        assert crisis_mock.await_count == 1
        new_review = (await db_session.execute(
            select(Review).filter(Review.source_review_id == "bf-new")
        )).scalars().first()
        assert smart_rules_mock.await_args.args[1] == new_review.id


class TestWebhookRetryBookkeeping:
    async def test_retry_updates_original_row_not_a_new_one(self, db_session):
        agency, _, _, _ = await _graph(db_session)
        endpoint = WebhookEndpoint(
            agency_id=agency.id, name="test-hook", url="https://example.test/hook",
            event_types=["*"], is_active=True,
        )
        db_session.add(endpoint)
        await db_session.flush()

        delivery = WebhookDelivery(
            endpoint_id=endpoint.id, event_type="review.created", payload={"k": "v"},
            success=False, attempt=1,
            next_retry_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db_session.add(delivery)
        await db_session.commit()

        # Simulate the retry recording another failure against the same row
        await _record_delivery(
            db_session, endpoint, "review.created", {"k": "v"},
            attempt=2, delivery_id=delivery.id, success=False, response_status=500,
        )
        await db_session.commit()

        rows = (await db_session.execute(
            select(WebhookDelivery).filter(WebhookDelivery.endpoint_id == endpoint.id)
        )).scalars().all()
        assert len(rows) == 1, "retry must not create a second delivery row"
        assert rows[0].attempt == 2
        assert rows[0].next_retry_at is not None

        # Final attempt exhausts retries
        await _record_delivery(
            db_session, endpoint, "review.created", {"k": "v"},
            attempt=MAX_RETRIES, delivery_id=delivery.id, success=False, response_status=500,
        )
        await db_session.commit()
        await db_session.refresh(delivery)
        assert delivery.attempt == MAX_RETRIES
        assert delivery.next_retry_at is None, "exhausted deliveries must leave the retry queue"

    async def test_next_retry_delays(self):
        assert _next_retry_at(MAX_RETRIES) is None
        d1 = _next_retry_at(1) - datetime.now(timezone.utc)
        assert timedelta(seconds=50) < d1 <= timedelta(seconds=60)
