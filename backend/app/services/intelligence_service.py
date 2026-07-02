import logging
import csv
import io
import random
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import selectinload
from app.models.customer_journey import CustomerProfile, Touchpoint, SupportTicket, OrderRecord, EmailFeedback
from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.tenant import Location, Client
from app.models.chat import ChatSession

logger = logging.getLogger(__name__)

# ── Data Import ────────────────────────────────────────────────────────

SEGMENT_OPTIONS = ["promoter", "at_risk", "detractor", "high_value", "lost", "new"]

async def import_crm_csv(db: AsyncSession, agency_id: UUID, content: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    errors = 0
    for row in reader:
        email = row.get("email", "").strip().lower()
        if not email:
            errors += 1
            continue
        result = await db.execute(
            select(CustomerProfile).filter(
                CustomerProfile.agency_id == agency_id,
                CustomerProfile.email == email,
            )
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.name = row.get("name", profile.name) or profile.name
            profile.phone = row.get("phone", profile.phone) or profile.phone
        else:
            profile = CustomerProfile(
                agency_id=agency_id,
                email=email,
                name=row.get("name"),
                phone=row.get("phone"),
                external_id=row.get("external_id"),
                last_activity_at=datetime.now(timezone.utc),
            )
            db.add(profile)
        imported += 1
    await db.commit()
    return {"imported": imported, "errors": errors}

async def import_orders_csv(db: AsyncSession, agency_id: UUID, content: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    errors = 0
    for row in reader:
        email = row.get("customer_email", "").strip().lower()
        if not email:
            errors += 1
            continue
        result = await db.execute(
            select(CustomerProfile).filter(
                CustomerProfile.agency_id == agency_id,
                CustomerProfile.email == email,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = CustomerProfile(
                agency_id=agency_id,
                email=email,
                name=row.get("customer_name"),
                last_activity_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            await db.flush()
        try:
            amount = float(row.get("amount", 0))
            order = OrderRecord(
                agency_id=agency_id,
                customer_id=profile.id,
                external_order_id=row.get("order_id"),
                amount=amount,
                order_date=datetime.fromisoformat(row.get("order_date", datetime.now(timezone.utc).isoformat())),
                description=row.get("description"),
            )
            db.add(order)
            profile.total_orders = (profile.total_orders or 0) + 1
            profile.total_spent = (profile.total_spent or 0) + amount
            profile.lifetime_value = profile.total_spent
            profile.last_activity_at = datetime.now(timezone.utc)
            imported += 1
        except (ValueError, KeyError) as e:
            logger.warning("Order import row error: %s", e)
            errors += 1
    await db.commit()
    return {"imported": imported, "errors": errors}

async def import_feedback_csv(db: AsyncSession, agency_id: UUID, content: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    errors = 0
    for row in reader:
        email = row.get("email", "").strip().lower()
        if not email:
            errors += 1
            continue
        result = await db.execute(
            select(CustomerProfile).filter(
                CustomerProfile.agency_id == agency_id,
                CustomerProfile.email == email,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = CustomerProfile(
                agency_id=agency_id,
                email=email,
                name=row.get("name"),
                last_activity_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            await db.flush()
        feedback = EmailFeedback(
            agency_id=agency_id,
            customer_id=profile.id,
            subject=row.get("subject"),
            body=row.get("body"),
            sentiment=row.get("sentiment"),
            received_at=datetime.fromisoformat(row.get("received_at", datetime.now(timezone.utc).isoformat())),
        )
        db.add(feedback)
        imported += 1
    await db.commit()
    return {"imported": imported, "errors": errors}

# ── Customer Segmentation ─────────────────────────────────────────────

async def run_segmentation(db: AsyncSession, agency_id: UUID) -> Dict[str, Any]:
    result = await db.execute(
        select(CustomerProfile).filter(CustomerProfile.agency_id == agency_id)
    )
    profiles = result.scalars().all()
    segments = {s: 0 for s in SEGMENT_OPTIONS}

    for profile in profiles:
        if profile.total_spent and profile.total_spent > 1000:
            profile.segment = "high_value"
        elif profile.total_orders and profile.total_orders > 5:
            profile.segment = "promoter"
        elif profile.churn_risk_score and profile.churn_risk_score > 0.7:
            profile.segment = "at_risk"
        elif profile.churn_risk_score and profile.churn_risk_score > 0.4:
            profile.segment = "detractor"
        elif profile.total_orders == 0:
            profile.segment = "new"
        else:
            profile.segment = "promoter"

        if profile.segment:
            segments[profile.segment] = segments.get(profile.segment, 0) + 1

    await db.commit()
    return {
        "segments": segments,
        "total_profiles": len(profiles),
    }

async def get_segmentation_summary(db: AsyncSession, agency_id: UUID) -> Dict[str, Any]:
    result = await db.execute(
        select(CustomerProfile.segment, func.count(CustomerProfile.id))
        .filter(CustomerProfile.agency_id == agency_id)
        .group_by(CustomerProfile.segment)
    )
    segments = {row[0] or "unclassified": row[1] for row in result.all()}
    total = sum(segments.values())
    return {"segments": segments, "total": total}

# ── AI Root-Cause Analysis ────────────────────────────────────────────

async def run_root_cause_analysis(db: AsyncSession, agency_id: UUID) -> Dict[str, Any]:
    from app.models.review import Review
    from app.models.sentiment import SentimentResult

    insights = []

    recent_reviews = await db.execute(
        select(Review, SentimentResult)
        .join(SentimentResult, Review.id == SentimentResult.review_id, isouter=True)
        .join(Location, Review.location_id == Location.id)
        .join(Client, Location.client_id == Client.id)
        .filter(Client.agency_id == agency_id, Review.created_at >= datetime.now(timezone.utc) - timedelta(days=90))
    )
    reviews = recent_reviews.all()

    negative_reviews = [r for r in reviews if r[1] and r[1].sentiment == "negative"] if reviews else []
    positive_reviews = [r for r in reviews if r[1] and r[1].sentiment == "positive"] if reviews else []

    total_reviews = len(reviews)
    negative_pct = round(len(negative_reviews) / max(total_reviews, 1) * 100, 1)

    ticket_result = await db.execute(
        select(func.count(SupportTicket.id))
        .filter(SupportTicket.agency_id == agency_id, SupportTicket.status == "open")
    )
    open_tickets = ticket_result.scalar() or 0

    if negative_pct > 30:
        insights.append({
            "type": "negative_trend",
            "severity": "high",
            "title": "Negative review rate is high",
            "detail": f"{negative_pct}% of recent reviews are negative. Review response process may need attention.",
            "recommendation": "Investigate common complaint patterns and update brand voice profiles.",
        })
    elif negative_pct > 15:
        insights.append({
            "type": "negative_trend",
            "severity": "medium",
            "title": "Negative reviews above average",
            "detail": f"{negative_pct}% of recent reviews are negative.",
            "recommendation": "Review recent negative feedback for operational patterns.",
        })

    if open_tickets > 20:
        insights.append({
            "type": "ticket_backlog",
            "severity": "medium",
            "title": f"{open_tickets} open support tickets",
            "detail": "Support ticket backlog may indicate unresolved customer issues affecting reviews.",
            "recommendation": "Prioritize ticket resolution and check if common review complaints match open tickets.",
        })

    low_rated = [r for r in negative_reviews if r[0].rating <= 2]
    topics_found = {}
    for review, sentiment_result in low_rated:
        if sentiment_result and sentiment_result.emotions:
            for emotion in (sentiment_result.emotions if isinstance(sentiment_result.emotions, list) else []):
                topics_found[str(emotion)] = topics_found.get(str(emotion), 0) + 1
        text = (review.text or "").lower()
        for topic in ["service", "staff", "price", "wait", "quality", "clean", "food", "delivery"]:
            if topic in text:
                topics_found[topic] = topics_found.get(topic, 0) + 1

    if topics_found:
        top_issues = sorted(topics_found.items(), key=lambda x: -x[1])[:3]
        issues_str = ", ".join([f"{t[0]} ({t[1]} mentions)" for t in top_issues])
        insights.append({
            "type": "common_themes",
            "severity": "info",
            "title": "Most common complaint themes",
            "detail": issues_str,
            "recommendation": "Address these operational areas to improve customer satisfaction.",
        })

    if not insights:
        insights.append({
            "type": "healthy",
            "severity": "info",
            "title": "No significant issues detected",
            "detail": "Review sentiment and support metrics look healthy.",
            "recommendation": "Continue monitoring and maintaining current practices.",
        })

    await _generate_ai_insights(agency_id, insights)

    return {
        "insights": insights,
        "total_reviews_analyzed": total_reviews,
        "negative_percentage": negative_pct,
        "open_tickets": open_tickets,
    }

async def _generate_ai_insights(agency_id: UUID, insights: List[Dict]) -> None:
    try:
        from app.ai.groq_client import get_groq_client
        client = get_groq_client()
        if not client:
            return
        prompt = (
            "You are a business intelligence analyst. Based on these insights, "
            "provide 1-2 specific actionable recommendations for the business owner. "
            f"Insights: {insights}\n\n"
            "Return as JSON: {\"recommendations\": [{\"action\": \"...\", \"impact\": \"...\", \"priority\": \"high|medium|low\"}]}"
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        import json
        ai_data = json.loads(resp.choices[0].message.content)
        insights.append({
            "type": "ai_recommendation",
            "severity": "info",
            "title": "AI-Powered Recommendation",
            "detail": ai_data.get("recommendations", [{}])[0].get("action", "") if ai_data.get("recommendations") else "",
            "recommendation": ai_data.get("recommendations", [{}])[0].get("impact", "") if ai_data.get("recommendations") else "",
        })
    except Exception as e:
        logger.warning("AI insight generation failed: %s", e)

# ── Enhanced Funnel ───────────────────────────────────────────────────

async def get_enhanced_funnel(db: AsyncSession, agency_id: UUID, days: int = 90) -> Dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    profiles = await db.execute(
        select(func.count(CustomerProfile.id)).filter(CustomerProfile.agency_id == agency_id)
    )
    total_customers = profiles.scalar() or 0

    locs = await db.execute(
        select(Location.id).select_from(Location).join(Client, Location.client_id == Client.id).filter(Client.agency_id == agency_id)
    )
    location_ids = [r[0] for r in locs.all()]

    reviewed_count = 0
    positive_count = 0
    if location_ids:
        reviews = await db.execute(
            select(func.count(func.distinct(Review.author_name)))
            .filter(Review.location_id.in_(location_ids))
        )
        reviewed_count = reviews.scalar() or 0
        pos = await db.execute(
            select(func.count(func.distinct(Review.id)))
            .join(SentimentResult, Review.id == SentimentResult.review_id)
            .filter(Review.location_id.in_(location_ids), SentimentResult.sentiment == "positive")
        )
        positive_count = pos.scalar() or 0

    chats = await db.execute(
        select(func.count(func.distinct(ChatSession.id)))
        .filter(ChatSession.created_at >= cutoff, ChatSession.session_type == "customer")
    )
    chatted = chats.scalar() or 0

    tickets = await db.execute(
        select(func.count(SupportTicket.id))
        .filter(SupportTicket.agency_id == agency_id, SupportTicket.created_at >= cutoff)
    )
    ticketed = tickets.scalar() or 0

    segments = await get_segmentation_summary(db, agency_id)
    orders = await db.execute(
        select(func.coalesce(func.sum(OrderRecord.amount), 0))
        .filter(OrderRecord.agency_id == agency_id)
    )
    total_revenue = orders.scalar() or 0.0

    return {
        "total_customers": total_customers,
        "reviewed": reviewed_count,
        "chatted": chatted,
        "ticketed": ticketed,
        "positive_sentiment": positive_count,
        "repeat_visitors": 0,
        "segment_breakdown": segments.get("segments", {}),
        "total_revenue": total_revenue,
    }
