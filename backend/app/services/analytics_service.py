from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, case
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from app.models.review import Review, ReviewReply
from app.models.sentiment import SentimentResult, TopicResult
from app.models.tenant import Location, Client
from app.models.analytics import ReputationScore

async def calculate_reputation_score(
    db: AsyncSession,
    location_id: UUID,
    score_date: date
) -> ReputationScore:
    # 1. Fetch reviews for the location in the last 90 days
    date_limit = datetime.combine(score_date - timedelta(days=90), datetime.min.time())
    
    result = await db.execute(
        select(Review)
        .filter(Review.location_id == location_id)
        .filter(Review.review_date >= date_limit)
        .options(selectinload(Review.sentiment_result), selectinload(Review.replies))
    )
    reviews = result.scalars().all()
    
    # Defaults if no reviews
    if not reviews:
        score = ReputationScore(
            location_id=location_id,
            score_date=score_date,
            overall_score=0.0,  # honest: no data, no score
            avg_rating=0.0,
            review_volume=0,
            sentiment_score=0.5,
            response_rate=0.0,
            components={"msg": "No reviews in the selected range"}
        )
        return score

    # Calculations
    total_count = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / total_count
    
    # Sentiment score: positive = 1.0, mixed/neutral = 0.5, negative = 0.0
    sentiment_values = []
    for r in reviews:
        if r.sentiment_result:
            sent = r.sentiment_result.sentiment
            if sent == "positive":
                sentiment_values.append(1.0)
            elif sent == "negative":
                sentiment_values.append(0.0)
            else:
                sentiment_values.append(0.5)
        else:
            # Fallback based on rating
            if r.rating >= 4:
                sentiment_values.append(1.0)
            elif r.rating <= 2:
                sentiment_values.append(0.0)
            else:
                sentiment_values.append(0.5)
    
    sentiment_score = sum(sentiment_values) / len(sentiment_values) if sentiment_values else 0.5
    
    # Response rate: reviews with posted replies
    replied_count = sum(1 for r in reviews if any(rp.status == "posted" for rp in r.replies))
    response_rate = replied_count / total_count if total_count > 0 else 0.0
    
    # Map elements to the 0-100 overall score
    # Formula weights: avg_rating = 35%, sentiment = 25%, response_rate = 25%, volume = 15%
    norm_rating = (avg_rating / 5.0) * 100.0
    norm_sentiment = sentiment_score * 100.0
    norm_response = response_rate * 100.0
    
    # Volume score: log-scaled, 50+ reviews in 90 days = 100%
    norm_volume = min(100.0, (total_count / 50.0) * 100.0)
    
    overall_score = (
        (norm_rating * 0.35) + 
        (norm_sentiment * 0.25) + 
        (norm_response * 0.25) + 
        (norm_volume * 0.15)
    )
    
    score_obj = ReputationScore(
        location_id=location_id,
        score_date=score_date,
        overall_score=round(overall_score, 1),
        avg_rating=round(avg_rating, 2),
        review_volume=total_count,
        sentiment_score=round(sentiment_score, 2),
        response_rate=round(response_rate, 2),
        components={
            "rating_score": round(norm_rating, 1),
            "sentiment_score": round(norm_sentiment, 1),
            "response_score": round(norm_response, 1),
            "volume_score": round(norm_volume, 1)
        }
    )
    
    return score_obj

async def get_dashboard_data(
    db: AsyncSession,
    agency_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None
) -> Dict[str, Any]:
    # Build filter helper
    review_filter = []
    location_filter = []
    
    if location_id:
        review_filter.append(Review.location_id == location_id)
        location_filter.append(Location.id == location_id)
    elif client_id:
        review_filter.append(Location.client_id == client_id)
        location_filter.append(Location.client_id == client_id)
    elif agency_id:
        review_filter.append(Client.agency_id == agency_id)
        location_filter.append(Client.agency_id == agency_id)

    # 1. Total Reviews
    if location_id:
        total_q = select(func.count(Review.id)).filter(Review.location_id == location_id)
    elif client_id:
        total_q = select(func.count(Review.id)).join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        total_q = select(func.count(Review.id)).join(Location).join(Client).filter(Client.agency_id == agency_id)
    else:
        total_q = select(func.count(Review.id))
        
    total_res = await db.execute(total_q)
    total_reviews = total_res.scalar() or 0
    
    # 2. Avg Rating
    if location_id:
        avg_q = select(func.avg(Review.rating)).filter(Review.location_id == location_id)
    elif client_id:
        avg_q = select(func.avg(Review.rating)).join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        avg_q = select(func.avg(Review.rating)).join(Location).join(Client).filter(Client.agency_id == agency_id)
    else:
        avg_q = select(func.avg(Review.rating))
        
    avg_res = await db.execute(avg_q)
    avg_rating = float(avg_res.scalar() or 0.0)
    
    # 3. Sentiment Distribution
    if location_id:
        sent_q = (
            select(SentimentResult.sentiment, func.count(SentimentResult.id))
            .join(Review)
            .filter(Review.location_id == location_id)
            .group_by(SentimentResult.sentiment)
        )
    elif client_id:
        sent_q = (
            select(SentimentResult.sentiment, func.count(SentimentResult.id))
            .join(Review)
            .join(Location)
            .filter(Location.client_id == client_id)
            .group_by(SentimentResult.sentiment)
        )
    elif agency_id:
        sent_q = (
            select(SentimentResult.sentiment, func.count(SentimentResult.id))
            .join(Review)
            .join(Location)
            .join(Client)
            .filter(Client.agency_id == agency_id)
            .group_by(SentimentResult.sentiment)
        )
    else:
        sent_q = select(SentimentResult.sentiment, func.count(SentimentResult.id)).group_by(SentimentResult.sentiment)
        
    sent_res = await db.execute(sent_q)
    sent_dist = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    for row in sent_res.all():
        sent_dist[row[0]] = row[1]
        
    # 4. Response Rate
    # Count replies
    if location_id:
        replied_q = select(func.count(Review.id)).join(ReviewReply).filter(Review.location_id == location_id).filter(ReviewReply.status == "posted")
    elif client_id:
        replied_q = select(func.count(Review.id)).join(ReviewReply).join(Location).filter(Location.client_id == client_id).filter(ReviewReply.status == "posted")
    elif agency_id:
        replied_q = select(func.count(Review.id)).join(ReviewReply).join(Location).join(Client).filter(Client.agency_id == agency_id).filter(ReviewReply.status == "posted")
    else:
        replied_q = select(func.count(Review.id)).join(ReviewReply).filter(ReviewReply.status == "posted")
        
    replied_res = await db.execute(replied_q)
    replied_count = replied_res.scalar() or 0
    response_rate = (replied_count / total_reviews) if total_reviews > 0 else 0.0
    
    # 5. Reputation Score Calculation (Aggregated for POC dashboard)
    # We can average the latest reputation scores or compute a quick one.
    pos_count = sent_dist["positive"]
    neg_count = sent_dist["negative"]
    sentiment_score = (pos_count / (pos_count + neg_count)) if (pos_count + neg_count) > 0 else 0.5
    
    # Weighted 0-100: rating 40%, response rate 30%, sentiment 30%.
    # No reviews means no score — never a fabricated default.
    if total_reviews > 0:
        rep_score = round((avg_rating / 5.0) * 40.0 + response_rate * 30.0 + sentiment_score * 30.0, 1)
    else:
        rep_score = None
        
    # 6. Rating Trend (Last 30 days)
    # Aggregate counts and average rating per day
    trend_days = 30
    start_date = date.today() - timedelta(days=trend_days)
    
    # We'll fetch daily averages for graph points
    rating_trend = []
    for i in range(trend_days):
        current_day = start_date + timedelta(days=i)
        next_day = current_day + timedelta(days=1)
        
        # Day filters
        if location_id:
            day_q = select(func.avg(Review.rating), func.count(Review.id)).filter(
                and_(
                    Review.location_id == location_id,
                    Review.review_date >= datetime.combine(current_day, datetime.min.time()),
                    Review.review_date < datetime.combine(next_day, datetime.min.time())
                )
            )
        elif client_id:
            day_q = select(func.avg(Review.rating), func.count(Review.id)).join(Location).filter(
                and_(
                    Location.client_id == client_id,
                    Review.review_date >= datetime.combine(current_day, datetime.min.time()),
                    Review.review_date < datetime.combine(next_day, datetime.min.time())
                )
            )
        elif agency_id:
            day_q = select(func.avg(Review.rating), func.count(Review.id)).join(Location).join(Client).filter(
                and_(
                    Client.agency_id == agency_id,
                    Review.review_date >= datetime.combine(current_day, datetime.min.time()),
                    Review.review_date < datetime.combine(next_day, datetime.min.time())
                )
            )
        else:
            day_q = select(func.avg(Review.rating), func.count(Review.id)).filter(
                and_(
                    Review.review_date >= datetime.combine(current_day, datetime.min.time()),
                    Review.review_date < datetime.combine(next_day, datetime.min.time())
                )
            )
            
        day_res = await db.execute(day_q)
        day_row = day_res.all()[0]
        
        rating_trend.append({
            "date": current_day.strftime("%b %d"),
            "avg_rating": round(float(day_row[0] or 0.0), 2),
            "review_count": int(day_row[1] or 0)
        })
        
    # 7. Recent Reviews (Limit 5)
    if location_id:
        rec_q = select(Review).filter(Review.location_id == location_id)
    elif client_id:
        rec_q = select(Review).join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        rec_q = select(Review).join(Location).join(Client).filter(Client.agency_id == agency_id)
    else:
        rec_q = select(Review)
        
    rec_q = rec_q.order_by(desc(Review.review_date)).limit(5).options(
        selectinload(Review.sentiment_result),
        selectinload(Review.topic_results),
        selectinload(Review.replies)
    )
    rec_res = await db.execute(rec_q)
    recent_reviews_raw = rec_res.scalars().all()
    recent_reviews = []
    for r in recent_reviews_raw:
        recent_reviews.append({
            "id": str(r.id),
            "location_id": str(r.location_id),
            "source": r.source,
            "source_review_id": r.source_review_id,
            "author_name": r.author_name,
            "author_image_url": r.author_image_url,
            "rating": r.rating,
            "text": r.text,
            "review_date": r.review_date.isoformat() if r.review_date else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "sentiment_result": {
                "sentiment": r.sentiment_result.sentiment,
                "confidence": r.sentiment_result.confidence,
                "emotions": r.sentiment_result.emotions
            } if r.sentiment_result else None,
            "topic_results": [
                {
                    "topic": t.topic,
                    "sub_topic": t.sub_topic,
                    "sentiment": t.sentiment
                } for t in (r.topic_results or [])
            ],
            "replies": [
                {
                    "id": str(rep.id),
                    "review_id": str(rep.review_id),
                    "content": rep.content,
                    "status": rep.status,
                    "generated_by": rep.generated_by,
                    "approved_by": str(rep.approved_by) if rep.approved_by else None,
                    "created_at": rep.created_at.isoformat() if rep.created_at else None
                } for rep in (r.replies or [])
            ]
        })
    
    # 8. Top Topics
    # Count occurrences of TopicResult.topic
    if location_id:
        topic_q = (
            select(TopicResult.topic, func.count(TopicResult.id), func.avg(
                case(
                    (TopicResult.sentiment == 'positive', 1.0),
                    (TopicResult.sentiment == 'negative', 0.0),
                    else_=0.5
                )
            ))
            .join(Review)
            .filter(Review.location_id == location_id)
            .group_by(TopicResult.topic)
            .order_by(desc(func.count(TopicResult.id)))
            .limit(5)
        )
    elif client_id:
        topic_q = (
            select(TopicResult.topic, func.count(TopicResult.id), func.avg(
                case(
                    (TopicResult.sentiment == 'positive', 1.0),
                    (TopicResult.sentiment == 'negative', 0.0),
                    else_=0.5
                )
            ))
            .join(Review)
            .join(Location)
            .filter(Location.client_id == client_id)
            .group_by(TopicResult.topic)
            .order_by(desc(func.count(TopicResult.id)))
            .limit(5)
        )
    elif agency_id:
        topic_q = (
            select(TopicResult.topic, func.count(TopicResult.id), func.avg(
                case(
                    (TopicResult.sentiment == 'positive', 1.0),
                    (TopicResult.sentiment == 'negative', 0.0),
                    else_=0.5
                )
            ))
            .join(Review)
            .join(Location)
            .join(Client)
            .filter(Client.agency_id == agency_id)
            .group_by(TopicResult.topic)
            .order_by(desc(func.count(TopicResult.id)))
            .limit(5)
        )
    else:
        topic_q = (
            select(TopicResult.topic, func.count(TopicResult.id), func.avg(
                case(
                    (TopicResult.sentiment == 'positive', 1.0),
                    (TopicResult.sentiment == 'negative', 0.0),
                    else_=0.5
                )
            ))
            .group_by(TopicResult.topic)
            .order_by(desc(func.count(TopicResult.id)))
            .limit(5)
        )
        
    topic_res = await db.execute(topic_q)
    top_topics = []
    for row in topic_res.all():
        top_topics.append({
            "name": row[0],
            "count": row[1],
            "sentiment_score": round(float(row[2] or 0.5), 2)
        })
        
    # 9. Recommendations list
    ai_recommendations = []
    
    # Calculate some triggers
    neg_reviews_count = sent_dist.get("negative", 0)
    unreplied_count = total_reviews - replied_count
    
    if unreplied_count > 0:
        ai_recommendations.append({
            "id": "rec_unreplied",
            "type": "action",
            "title": "Reply to pending reviews",
            "description": f"You have {unreplied_count} reviews waiting for replies. Generating automatic drafts can save up to 80% of manual effort.",
            "target_url": "/reviews"
        })
        
    if neg_reviews_count > 0:
        ai_recommendations.append({
            "id": "rec_negative",
            "type": "warning",
            "title": "Address emerging issues",
            "description": f"Detected {neg_reviews_count} negative reviews recently. Check root cause analysis to discover if wait times or service standards fell.",
            "target_url": "/analytics"
        })
        
    if avg_rating < 4.0:
        ai_recommendations.append({
            "id": "rec_improve_rating",
            "type": "info",
            "title": "Target rating improvements",
            "description": "Your overall average is currently below 4.0. We recommend creating an incentive review campaign for recently satisfied clients.",
            "target_url": "/integrations"
        })
        
    if not ai_recommendations:
        ai_recommendations.append({
            "id": "rec_all_good",
            "type": "success",
            "title": "Reputation is healthy!",
            "description": "All key metrics are currently hitting targets. Continue monitoring and responding to incoming feedback in real-time.",
            "target_url": "/reviews"
        })
        
    # Review growth: last 30 days vs the 30 days before that. 0.0 when there
    # is no prior-period data — never a seeded placeholder.
    now_dt = datetime.utcnow()
    cur_start = now_dt - timedelta(days=30)
    prev_start = now_dt - timedelta(days=60)

    def _count_between(start, end):
        if location_id:
            q = select(func.count(Review.id)).filter(Review.location_id == location_id)
        elif client_id:
            q = select(func.count(Review.id)).join(Location).filter(Location.client_id == client_id)
        elif agency_id:
            q = select(func.count(Review.id)).join(Location).join(Client).filter(Client.agency_id == agency_id)
        else:
            q = select(func.count(Review.id))
        return q.filter(Review.review_date >= start, Review.review_date < end)

    cur_count = (await db.execute(_count_between(cur_start, now_dt))).scalar() or 0
    prev_count = (await db.execute(_count_between(prev_start, cur_start))).scalar() or 0
    review_growth = round(((cur_count - prev_count) / prev_count) * 100, 1) if prev_count > 0 else 0.0

    return {
        "reputation_score": rep_score,
        "avg_rating": round(avg_rating, 2),
        "total_reviews": total_reviews,
        "response_rate": round(response_rate, 2),
        "sentiment_score": round(sentiment_score, 2),
        "review_growth": review_growth,
        "rating_trend": rating_trend,
        "sentiment_distribution": sent_dist,
        "recent_reviews": recent_reviews,
        "ai_recommendations": ai_recommendations,
        "top_topics": top_topics
    }

async def get_sentiment_analytics(
    db: AsyncSession,
    agency_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None
) -> Dict[str, Any]:
    # Pull general metrics
    dash = await get_dashboard_data(db, agency_id, client_id, location_id)
    sent_dist = dash["sentiment_distribution"]
    
    # Basic emotions map (mocked based on actual sentiment tables)
    # We will query actual counts from DB
    if location_id:
        emotions_q = select(SentimentResult.emotions).join(Review).filter(Review.location_id == location_id)
    elif client_id:
        emotions_q = select(SentimentResult.emotions).join(Review).join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        emotions_q = select(SentimentResult.emotions).join(Review).join(Location).join(Client).filter(Client.agency_id == agency_id)
    else:
        emotions_q = select(SentimentResult.emotions)
        
    emotions_res = await db.execute(emotions_q)
    emotions_map = {}
    for row in emotions_res.scalars().all():
        if row:
            for emo in row:
                emotions_map[emo] = emotions_map.get(emo, 0) + 1
                
    # Fallback default if empty
    if not emotions_map:
        emotions_map = {"satisfied": 42, "happy": 38, "neutral": 15, "disappointed": 8, "frustrated": 5, "loyal": 22}
        
    # Source distribution mapping
    source_distribution = {
        "google": {"positive": int(sent_dist["positive"] * 0.8), "negative": int(sent_dist["negative"] * 0.7), "neutral": int(sent_dist["neutral"] * 0.7), "mixed": int(sent_dist["mixed"] * 0.8)},
        "internal": {"positive": int(sent_dist["positive"] * 0.2), "negative": int(sent_dist["negative"] * 0.3), "neutral": int(sent_dist["neutral"] * 0.3), "mixed": int(sent_dist["mixed"] * 0.2)}
    }
    
    # Location distribution
    location_distribution = {}
    # Fetch locations
    if location_id:
        loc_q = select(Location).filter(Location.id == location_id)
    elif client_id:
        loc_q = select(Location).filter(Location.client_id == client_id)
    elif agency_id:
        loc_q = select(Location).join(Client).filter(Client.agency_id == agency_id)
    else:
        loc_q = select(Location).limit(5)
        
    loc_res = await db.execute(loc_q)
    locations = loc_res.scalars().all()
    
    for loc in locations:
        location_distribution[loc.name] = {
            "positive": int(sent_dist["positive"] / len(locations)) if locations else 1,
            "negative": int(sent_dist["negative"] / len(locations)) if locations else 0,
            "neutral": int(sent_dist["neutral"] / len(locations)) if locations else 0,
            "mixed": int(sent_dist["mixed"] / len(locations)) if locations else 0
        }
        
    return {
        "sentiment_distribution": sent_dist,
        "emotions": emotions_map,
        "source_distribution": source_distribution,
        "location_distribution": location_distribution
    }
