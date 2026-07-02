import logging
from uuid import UUID
from datetime import datetime, date, timedelta
import random
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, delete
from app.models.tenant import Location
from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.competitor import Competitor, CompetitorReview, CompetitorAnalysis, CompetitorPriceRecord, CompetitorLocationAlert
from app.ai.groq_client import get_groq_client

logger = logging.getLogger(__name__)

MOCK_REVIEWS_TEMPLATES = [
    {"text": "Absolutely delicious! Best place in town, friendly staff.", "rating": 5, "sentiment": "positive"},
    {"text": "Great atmosphere and prompt service.", "rating": 5, "sentiment": "positive"},
    {"text": "The food was okay, but wait times were incredibly long. Took 45 minutes to get seated.", "rating": 2, "sentiment": "negative"},
    {"text": "Overpriced for what it is, and the manager was rude.", "rating": 2, "sentiment": "negative"},
    {"text": "Clean establishment, standard food. Nothing special.", "rating": 3, "sentiment": "neutral"},
    {"text": "Decent experience. Staff was nice but they forgot my drink.", "rating": 3, "sentiment": "mixed"},
    {"text": "Highly recommend the specials! Super fresh ingredients.", "rating": 5, "sentiment": "positive"},
    {"text": "Disappointed with the billing. They added hidden charges.", "rating": 2, "sentiment": "negative"},
    {"text": "We love coming here on weekends. Solid experience.", "rating": 4, "sentiment": "positive"},
    {"text": "Parking is a nightmare but the desserts make up for it.", "rating": 4, "sentiment": "mixed"},
    {"text": "Cold food and slow service. Never coming back.", "rating": 1, "sentiment": "negative"},
    {"text": "The place is amazing! Excellent customer service.", "rating": 5, "sentiment": "positive"},
]

async def add_competitor(db: AsyncSession, location_id: UUID, name: str, google_place_id: Optional[str] = None) -> Competitor:
    # 1. Create competitor
    competitor = Competitor(
        location_id=location_id,
        name=name,
        google_place_id=google_place_id
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)

    # 2. Seed mock reviews for competitor (spread over 30 days)
    now = datetime.utcnow()
    reviews_to_add = []
    
    # Select a random subset of templates
    templates = random.sample(MOCK_REVIEWS_TEMPLATES, 10)
    for i, t in enumerate(templates):
        review_date = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
        comp_review = CompetitorReview(
            competitor_id=competitor.id,
            author_name=f"Customer {i+1}",
            rating=t["rating"],
            text=t["text"],
            review_date=review_date,
            sentiment=t["sentiment"]
        )
        reviews_to_add.append(comp_review)
        
    db.add_all(reviews_to_add)
    await db.commit()
    return competitor

async def delete_competitor(db: AsyncSession, competitor_id: UUID) -> bool:
    stmt = select(Competitor).where(Competitor.id == competitor_id)
    result = await db.execute(stmt)
    competitor = result.scalar_one_or_none()
    if not competitor:
        return False
    await db.delete(competitor)
    await db.commit()
    return True

async def get_competitors(db: AsyncSession, location_id: UUID) -> List[Competitor]:
    stmt = select(Competitor).where(Competitor.location_id == location_id).order_by(Competitor.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_competitor_analytics(db: AsyncSession, location_id: UUID) -> Dict[str, Any]:
    # 1. Fetch client metrics
    # Avg rating
    client_avg_q = select(func.avg(Review.rating), func.count(Review.id)).filter(Review.location_id == location_id)
    client_avg_res = await db.execute(client_avg_q)
    client_row = client_avg_res.all()[0]
    client_avg = float(client_row[0] or 0.0)
    client_count = int(client_row[1] or 0)
    
    # Sentiment distribution
    client_sent_q = (
        select(SentimentResult.sentiment, func.count(SentimentResult.id))
        .join(Review)
        .filter(Review.location_id == location_id)
        .group_by(SentimentResult.sentiment)
    )
    client_sent_res = await db.execute(client_sent_q)
    client_sent_dist = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    for row in client_sent_res.all():
        client_sent_dist[row[0]] = row[1]
        
    # Get location name
    loc_q = select(Location.name).filter(Location.id == location_id)
    loc_res = await db.execute(loc_q)
    location_name = loc_res.scalar() or "Our Business"

    client_metrics = {
        "name": f"{location_name} (You)",
        "avg_rating": round(client_avg, 2),
        "review_count": client_count,
        "sentiment_distribution": client_sent_dist
    }

    # 2. Fetch competitors metrics
    competitors_stmt = select(Competitor).where(Competitor.location_id == location_id)
    comp_result = await db.execute(competitors_stmt)
    competitors = comp_result.scalars().all()
    
    competitor_metrics_list = []
    
    for comp in competitors:
        comp_avg_q = select(func.avg(CompetitorReview.rating), func.count(CompetitorReview.id)).filter(CompetitorReview.competitor_id == comp.id)
        comp_avg_res = await db.execute(comp_avg_q)
        comp_row = comp_avg_res.all()[0]
        comp_avg = float(comp_row[0] or 0.0)
        comp_count = int(comp_row[1] or 0)
        
        comp_sent_q = (
            select(CompetitorReview.sentiment, func.count(CompetitorReview.id))
            .filter(CompetitorReview.competitor_id == comp.id)
            .group_by(CompetitorReview.sentiment)
        )
        comp_sent_res = await db.execute(comp_sent_q)
        comp_sent_dist = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        for row in comp_sent_res.all():
            if row[0]:
                comp_sent_dist[row[0]] = row[1]
                
        competitor_metrics_list.append({
            "id": str(comp.id),
            "name": comp.name,
            "avg_rating": round(comp_avg, 2),
            "review_count": comp_count,
            "sentiment_distribution": comp_sent_dist
        })
        
    return {
        "client": client_metrics,
        "competitors": competitor_metrics_list
    }

async def run_competitor_ai_analysis(db: AsyncSession, location_id: UUID) -> CompetitorAnalysis:
    # 1. Fetch recent client reviews
    client_rev_stmt = select(Review.text, Review.rating).filter(Review.location_id == location_id).order_by(Review.review_date.desc()).limit(15)
    client_rev_res = await db.execute(client_rev_stmt)
    client_revs = [f"Rating: {r.rating}* | Text: {r.text or 'No text'}" for r in client_rev_res.all()]
    
    # 2. Fetch competitor reviews
    comp_rev_stmt = (
        select(Competitor.name, CompetitorReview.rating, CompetitorReview.text)
        .join(CompetitorReview)
        .filter(Competitor.location_id == location_id)
        .order_by(CompetitorReview.review_date.desc())
        .limit(30)
    )
    comp_rev_res = await db.execute(comp_rev_stmt)
    comp_revs = [f"Competitor: {r.name} | Rating: {r.rating}* | Text: {r.text or 'No text'}" for r in comp_rev_res.all()]
    
    client_reviews_str = "\n".join(client_revs) if client_revs else "No reviews recorded yet."
    competitor_reviews_str = "\n".join(comp_revs) if comp_revs else "No competitor reviews recorded yet."
    
    # 3. Formulate AI Analysis
    groq = get_groq_client()
    
    system_prompt = (
        "You are the ReputationOS AI Competitor Analyst. "
        "Analyze customer feedback for our business and competitors to extract competitive intelligence. "
        "Highlight exactly where our business stands out (strengths), where we fall behind (weaknesses), "
        "and market opportunities based on competitors' negative feedback. "
        "You MUST respond in JSON format matching the schema exactly: "
        "{\n"
        "  \"strengths\": [\"string\"],\n"
        "  \"weaknesses\": [\"string\"],\n"
        "  \"opportunities\": [\"string\"],\n"
        "  \"summary\": \"string\"\n"
        "}"
    )
    
    user_prompt = (
        f"OUR BUSINESS REVIEWS:\n{client_reviews_str}\n\n"
        f"COMPETITORS REVIEWS:\n{competitor_reviews_str}\n\n"
        f"Perform the analysis and output JSON."
    )
    
    analysis_data = None
    if groq.client:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        completion = await groq.chat_completion(messages, temperature=0.1, response_json=True)
        if completion:
            try:
                # Clean block code wrapping
                cleaned = completion.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                    
                analysis_data = json.loads(cleaned)
            except Exception as e:
                logger.error(f"Failed to parse competitor analysis JSON: {e}")
                
    if not analysis_data:
        # Fallback to local heuristic / mock response
        # Create smart mock details based on review content
        has_pricing_complaints = "price" in competitor_reviews_str.lower() or "charge" in competitor_reviews_str.lower()
        has_waiting_complaints = "wait" in competitor_reviews_str.lower() or "slow" in competitor_reviews_str.lower()
        
        strengths = ["Friendly staff and personalized customer service.", "High quality ingredients and delicious meals."]
        weaknesses = ["Slightly higher pricing compared to immediate local fast-food alternatives."]
        
        opportunities = []
        if has_waiting_complaints:
            opportunities.append("Emphasize our short wait times and reservation speed in marketing campaigns since competitors are receiving complaints about slow seating.")
        if has_pricing_complaints:
            opportunities.append("Position our business as the premium quality choice or highlight lunch value specials to capture cost-conscious diners from competitors.")
            
        if not opportunities:
            opportunities.append("Target competitor customers by promoting positive testimonials regarding speed of service and staff responsiveness.")
            
        analysis_data = {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "summary": "Our business retains high customer loyalty due to exceptional service, while local competitors suffer from wait-time bottlenecks and service inconsistency."
        }
        
    # 4. Save analysis to database
    today = date.today()
    
    # Check if analysis exists for today
    exist_stmt = select(CompetitorAnalysis).filter(and_(CompetitorAnalysis.location_id == location_id, CompetitorAnalysis.analysis_date == today))
    exist_res = await db.execute(exist_stmt)
    analysis = exist_res.scalar_one_or_none()
    
    if analysis:
        analysis.strengths = analysis_data["strengths"]
        analysis.weaknesses = analysis_data["weaknesses"]
        analysis.opportunities = analysis_data["opportunities"]
        analysis.summary = analysis_data["summary"]
    else:
        analysis = CompetitorAnalysis(
            location_id=location_id,
            analysis_date=today,
            strengths=analysis_data["strengths"],
            weaknesses=analysis_data["weaknesses"],
            opportunities=analysis_data["opportunities"],
            summary=analysis_data["summary"]
        )
        db.add(analysis)
        
    await db.commit()
    await db.refresh(analysis)
    return analysis

async def get_latest_competitor_analysis(db: AsyncSession, location_id: UUID) -> Optional[CompetitorAnalysis]:
    stmt = select(CompetitorAnalysis).filter(CompetitorAnalysis.location_id == location_id).order_by(CompetitorAnalysis.analysis_date.desc()).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

# ── Pricing Monitoring ─────────────────────────────────────────────────

async def record_competitor_price(db: AsyncSession, competitor_id: UUID, price: float, description: Optional[str] = None) -> CompetitorPriceRecord:
    record = CompetitorPriceRecord(
        competitor_id=competitor_id,
        price=price,
        description=description,
        recorded_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

async def get_competitor_prices(db: AsyncSession, competitor_id: UUID, limit: int = 20) -> List[CompetitorPriceRecord]:
    result = await db.execute(
        select(CompetitorPriceRecord)
        .filter(CompetitorPriceRecord.competitor_id == competitor_id)
        .order_by(CompetitorPriceRecord.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_all_price_changes(db: AsyncSession, location_id: UUID, days: int = 90) -> List[Dict[str, Any]]:
    comps = await db.execute(select(Competitor).filter(Competitor.location_id == location_id))
    results = []
    cutoff = datetime.utcnow() - timedelta(days=days)
    for comp in comps.scalars().all():
        records = await db.execute(
            select(CompetitorPriceRecord)
            .filter(CompetitorPriceRecord.competitor_id == comp.id, CompetitorPriceRecord.recorded_at >= cutoff)
            .order_by(CompetitorPriceRecord.recorded_at.desc())
        )
        for r in records.scalars().all():
            results.append({
                "id": str(r.id),
                "competitor_id": str(comp.id),
                "competitor_name": comp.name,
                "price": r.price,
                "description": r.description,
                "recorded_at": r.recorded_at,
            })
    return results

# ── Location Alerts ────────────────────────────────────────────────────

async def create_location_alert(db: AsyncSession, agency_id: UUID, competitor_name: str, alert_type: str, description: Optional[str] = None, source_url: Optional[str] = None) -> CompetitorLocationAlert:
    alert = CompetitorLocationAlert(
        agency_id=agency_id,
        competitor_name=competitor_name,
        alert_type=alert_type,
        description=description,
        source_url=source_url,
        detected_at=datetime.utcnow(),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert

async def list_location_alerts(db: AsyncSession, agency_id: UUID, unread_only: bool = False) -> List[CompetitorLocationAlert]:
    query = select(CompetitorLocationAlert).filter(CompetitorLocationAlert.agency_id == agency_id)
    if unread_only:
        query = query.filter(CompetitorLocationAlert.is_read == False)
    query = query.order_by(CompetitorLocationAlert.detected_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()

async def mark_alert_read(db: AsyncSession, alert_id: UUID, agency_id: UUID) -> bool:
    result = await db.execute(
        select(CompetitorLocationAlert).filter(CompetitorLocationAlert.id == alert_id, CompetitorLocationAlert.agency_id == agency_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        return False
    alert.is_read = True
    await db.commit()
    return True

# ── Weekly AI Report ───────────────────────────────────────────────────

async def generate_weekly_competitor_report(db: AsyncSession, location_id: UUID) -> Dict[str, Any]:
    from datetime import date, timedelta

    comps = await db.execute(select(Competitor).filter(Competitor.location_id == location_id))
    competitors = comps.scalars().all()

    week_ago = datetime.utcnow() - timedelta(days=7)
    report_data = []

    for comp in competitors:
        price_records = await db.execute(
            select(CompetitorPriceRecord)
            .filter(CompetitorPriceRecord.competitor_id == comp.id, CompetitorPriceRecord.recorded_at >= week_ago)
            .order_by(CompetitorPriceRecord.recorded_at.desc())
        )
        prices = price_records.scalars().all()

        avg_rating = await db.execute(
            select(func.avg(CompetitorReview.rating)).filter(CompetitorReview.competitor_id == comp.id)
        )
        avg = avg_rating.scalar()
        review_count = await db.execute(
            select(func.count(CompetitorReview.id)).filter(CompetitorReview.competitor_id == comp.id)
        )

        report_data.append({
            "name": comp.name,
            "avg_rating": round(float(avg), 2) if avg else None,
            "review_count": review_count.scalar() or 0,
            "price_changes": [
                {"price": p.price, "date": p.recorded_at.isoformat() if p.recorded_at else None, "note": p.description}
                for p in prices
            ],
        })

    from app.ai.groq_client import get_groq_client
    client = get_groq_client()
    ai_summary = None
    if client:
        try:
            prompt = (
                "You are a competitive intelligence analyst. Based on this weekly data, "
                "write a brief executive summary (2-3 sentences) highlighting key competitive threats and opportunities.\n\n"
                f"Data: {report_data}\n\nReturn as JSON: {{\"summary\": \"...\", \"top_threat\": \"...\", \"top_opportunity\": \"...\"}}"
            )
            resp = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
                response_json=True,
            )
            import json
            if resp:
                ai_summary = json.loads(resp)
        except Exception as e:
            logger.warning("AI report generation failed: %s", e)

    return {
        "report_date": date.today().isoformat(),
        "location_id": str(location_id),
        "total_competitors": len(competitors),
        "competitors": report_data,
        "ai_insights": ai_summary or {"summary": "Run analysis to get AI-powered insights."},
    }
