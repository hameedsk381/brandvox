"""Regression tests for the July 2026 core-logic review fixes:

1. Billing webhook requires a valid raw-body HMAC signature
2. Agency admins cannot self-modify subscription state
3. Reputation score is 0-100 and None (never fabricated) without reviews
4. Reply generation refuses template fallback in production
5. Replies are validated against Google's length limit
6. Sentiment results record which analyzer produced them
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.core.auth import create_access_token, hash_password
from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.tenant import Agency, Client, Location
from app.models.user import User
from app.services.analytics_service import get_dashboard_data
from app.services.billing_service import billing_service
from app.services.reply_service import GOOGLE_REPLY_MAX_CHARS, save_reply
from app.services.sentiment_service import analyze_review_sentiment_and_topics

pytestmark = pytest.mark.asyncio

WEBHOOK_SECRET = "test-webhook-secret"


def _settings_with_secret(**overrides):
    from app.config import get_settings
    base = get_settings()
    values = {k: getattr(base, k) for k in base.model_fields}
    values.update(overrides)
    return SimpleNamespace(**values)


async def _agency_graph(db, slug="core-agency"):
    agency = Agency(name=f"Agency {slug}", slug=slug, settings={})
    db.add(agency)
    await db.flush()
    client_row = Client(agency_id=agency.id, name=f"Client {slug}", industry="Restaurant", settings={})
    db.add(client_row)
    await db.flush()
    location = Location(client_id=client_row.id, name=f"Location {slug}", timezone="UTC")
    db.add(location)
    admin = User(
        email=f"admin@{slug}.test",
        hashed_password=hash_password("Password1!"),
        name="Agency Admin",
        role="agency_admin",
        agency_id=agency.id,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    return agency, client_row, location, admin


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token(data={'sub': user.email})}"}


class TestBillingWebhookSignature:
    def _signed(self, body: bytes) -> str:
        return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    def test_unsigned_rejected(self):
        with patch("app.services.billing_service.get_settings",
                   return_value=_settings_with_secret(RAZORPAY_WEBHOOK_SECRET=WEBHOOK_SECRET)):
            assert billing_service.verify_webhook_signature(b'{"event":"payment.captured"}', None) is False

    def test_bad_signature_rejected(self):
        with patch("app.services.billing_service.get_settings",
                   return_value=_settings_with_secret(RAZORPAY_WEBHOOK_SECRET=WEBHOOK_SECRET)):
            assert billing_service.verify_webhook_signature(b'{"a":1}', "deadbeef") is False

    def test_valid_signature_accepted(self):
        body = b'{"event":"payment.captured"}'
        with patch("app.services.billing_service.get_settings",
                   return_value=_settings_with_secret(RAZORPAY_WEBHOOK_SECRET=WEBHOOK_SECRET)):
            assert billing_service.verify_webhook_signature(body, self._signed(body)) is True

    def test_no_secret_configured_rejects_everything(self):
        with patch("app.services.billing_service.get_settings",
                   return_value=_settings_with_secret(RAZORPAY_WEBHOOK_SECRET="", RAZORPAY_KEY_SECRET="")):
            assert billing_service.verify_webhook_signature(b"{}", "anything") is False

    async def test_endpoint_rejects_forged_upgrade(self, client, db_session):
        """The original exploit: unsigned payment.captured granting a plan."""
        agency, _, _, _ = await _agency_graph(db_session, slug="forge-target")
        forged = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"notes": {"agency_id": str(agency.id), "plan": "enterprise"}}}},
        }
        response = await client.post("/api/billing/webhook", json=forged)
        assert response.status_code == 400
        await db_session.refresh(agency)
        assert agency.subscription_plan == "trial"


class TestBillingSelfServiceLockdown:
    async def test_agency_admin_cannot_change_own_plan(self, client, db_session):
        _, _, _, admin = await _agency_graph(db_session, slug="self-upgrade")
        response = await client.patch(
            "/api/billing/update",
            json={"subscription_plan": "enterprise", "subscription_status": "active"},
            headers=_auth(admin),
        )
        assert response.status_code == 403


class TestReputationScoreHonesty:
    async def test_no_reviews_means_no_score(self, db_session):
        agency, _, _, _ = await _agency_graph(db_session, slug="empty-tenant")
        data = await get_dashboard_data(db_session, agency_id=agency.id)
        assert data["reputation_score"] is None
        assert data["review_growth"] == 0.0

    async def test_score_is_bounded_0_100(self, db_session):
        agency, _, location, _ = await _agency_graph(db_session, slug="scored-tenant")
        db_session.add(Review(
            location_id=location.id, source="manual", source_review_id="score-1",
            author_name="R", rating=5, text="perfect", review_date=datetime.now(timezone.utc),
        ))
        await db_session.commit()

        data = await get_dashboard_data(db_session, agency_id=agency.id)
        # 5★ avg (40) + 0 response rate (0) + neutral sentiment default (15)
        assert data["reputation_score"] == 55.0
        assert 0 <= data["reputation_score"] <= 100


class TestReplyGenerationProductionSafety:
    async def test_no_template_fallback_in_production(self):
        from app.ai.review_reply import generate_reply
        with patch("app.config.get_settings",
                   return_value=_settings_with_secret(ENVIRONMENT="production", DEMO_MODE=False)):
            options = await generate_reply(
                review_text="Great!", rating=5, brand_voice={}, business_name="B", industry="Restaurant",
            )
        assert options == []

    async def test_templates_still_available_in_development(self):
        from app.ai.review_reply import generate_reply
        with patch("app.config.get_settings",
                   return_value=_settings_with_secret(ENVIRONMENT="development", DEMO_MODE=False)):
            options = await generate_reply(
                review_text="Great!", rating=5, brand_voice={}, business_name="B", industry="Restaurant",
            )
        assert len(options) == 2


class TestReplyLengthGuard:
    async def test_oversized_reply_rejected(self, db_session):
        _, _, location, _ = await _agency_graph(db_session, slug="long-reply")
        review = Review(
            location_id=location.id, source="manual", source_review_id="long-1",
            author_name="R", rating=4, text="ok", review_date=datetime.now(timezone.utc),
        )
        db_session.add(review)
        await db_session.commit()

        with pytest.raises(ValueError, match="character limit"):
            await save_reply(db_session, review.id, "x" * (GOOGLE_REPLY_MAX_CHARS + 1))

    async def test_empty_reply_rejected(self, db_session):
        _, _, location, _ = await _agency_graph(db_session, slug="empty-reply")
        review = Review(
            location_id=location.id, source="manual", source_review_id="empty-1",
            author_name="R", rating=4, text="ok", review_date=datetime.now(timezone.utc),
        )
        db_session.add(review)
        await db_session.commit()

        with pytest.raises(ValueError, match="empty"):
            await save_reply(db_session, review.id, "   ")


class TestCompetitorSampleLabeling:
    async def test_seeded_competitor_data_is_flagged(self, db_session):
        from app.services.competitor_service import add_competitor, get_competitor_analytics

        _, _, location, _ = await _agency_graph(db_session, slug="sample-comp")
        await add_competitor(db_session, location.id, "Rival Diner")

        analytics = await get_competitor_analytics(db_session, location.id)
        assert analytics["is_sample_data"] is True

    async def test_no_competitors_means_no_sample_flag(self, db_session):
        from app.services.competitor_service import get_competitor_analytics

        _, _, location, _ = await _agency_graph(db_session, slug="no-comp")
        analytics = await get_competitor_analytics(db_session, location.id)
        assert analytics["is_sample_data"] is False


class TestSentimentModelMarker:
    async def test_keyword_fallback_is_tagged(self, db_session):
        """Without a Groq key (test env), sentiment must be tagged keyword_fallback."""
        _, _, location, _ = await _agency_graph(db_session, slug="tagged-sentiment")
        review = Review(
            location_id=location.id, source="manual", source_review_id="tag-1",
            author_name="R", rating=5, text="great food", review_date=datetime.now(timezone.utc),
        )
        db_session.add(review)
        await db_session.commit()

        ok = await analyze_review_sentiment_and_topics(db_session, review.id)
        assert ok is True
        result = (await db_session.execute(
            select(SentimentResult).filter(SentimentResult.review_id == review.id)
        )).scalars().first()
        assert result is not None
        assert result.model == "keyword_fallback"
