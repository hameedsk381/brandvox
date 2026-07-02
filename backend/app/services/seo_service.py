import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from app.models.seo import SeoProfile, KeywordRanking, CitationRecord
from app.models.competitor import Competitor, CompetitorMapsRanking, GbpPostSchedule
from app.schemas.seo import KeywordRankingCreate, GbpPostScheduleCreate

logger = logging.getLogger(__name__)

# ── GBP Audit ─────────────────────────────────────────────────────────

async def run_gbp_audit(db: AsyncSession, location_id: UUID, agency_id: UUID) -> Dict[str, Any]:
    from app.models.tenant import Location, Client

    result = await db.execute(
        select(Location).filter(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    if not location:
        return {"error": "Location not found"}

    score = 0
    missing_fields = []
    max_score = 100

    if location.name:
        score += 15
    else:
        missing_fields.append("Business name")

    if location.address:
        score += 20
    else:
        missing_fields.append("Address")

    if location.google_place_id:
        score += 15
    else:
        missing_fields.append("Google Place ID")

    if location.timezone:
        score += 5
    else:
        missing_fields.append("Timezone")

    from app.models.review import Review
    review_count = await db.execute(
        select(func.count()).select_from(Review).filter(Review.location_id == location_id)
    )
    rc = review_count.scalar() or 0
    if rc > 0:
        score += min(rc * 2, 15)

    reply_count = await db.execute(
        select(func.count()).select_from(Review)
        .filter(Review.location_id == location_id, Review.replies.any())
    )
    rpc = reply_count.scalar() or 0
    response_rate = round((rpc / rc * 100) if rc > 0 else 0, 1)
    if response_rate > 80:
        score += 15
    elif response_rate > 50:
        score += 10
    elif response_rate > 20:
        score += 5
    else:
        missing_fields.append("Review responses (below 20%)")

    if location.phone:
        score += 10
    else:
        missing_fields.append("Phone number")

    if location.website:
        score += 5
    else:
        missing_fields.append("Website")

    completeness_score = min(score, max_score)

    existing = await db.execute(
        select(SeoProfile).filter(SeoProfile.location_id == location_id)
    )
    profile = existing.scalar_one_or_none()

    if profile:
        profile.gbp_completeness_score = completeness_score
        profile.gbp_missing_fields = missing_fields
        profile.gbp_response_rate = response_rate
        profile.last_audit_at = datetime.utcnow()
    else:
        profile = SeoProfile(
            location_id=location_id,
            gbp_completeness_score=completeness_score,
            gbp_missing_fields=missing_fields,
            gbp_response_rate=response_rate,
            last_audit_at=datetime.utcnow(),
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    recommendations = await _generate_seo_recommendations(completeness_score, missing_fields, response_rate, rc)

    return {
        "location_id": str(location_id),
        "completeness_score": completeness_score,
        "missing_fields": missing_fields,
        "photo_count": profile.gbp_photo_count,
        "post_count": profile.gbp_post_count,
        "response_rate": response_rate,
        "recommendations": recommendations,
    }

async def _generate_seo_recommendations(score: int, missing_fields: List[str], response_rate: float, review_count: int) -> List[str]:
    recs = []
    if score < 50:
        recs.append("Complete your Google Business Profile — fill in all missing fields to improve local search visibility.")
    for field in missing_fields:
        recs.append(f"Add your {field.lower()} to your Google Business Profile.")
    if response_rate < 50:
        recs.append(f"Respond to more reviews (currently {response_rate}%). Businesses that respond get 35% more reviews.")
    if review_count < 10:
        recs.append("Encourage more reviews. Use Review Campaigns to generate 5-star reviews from happy customers.")
    if 50 <= score < 80:
        recs.append("Your profile is decent. Add photos weekly and respond to every review to reach 80%+ completeness.")
    if score >= 80:
        recs.append("Your profile looks great! Maintain it with regular photo updates and review responses.")
    if not recs:
        recs.append("Run an audit to get personalized SEO recommendations.")
    return recs

# ── Keyword Rankings ───────────────────────────────────────────────────

async def list_keywords(db: AsyncSession, location_id: UUID) -> List[KeywordRanking]:
    result = await db.execute(
        select(KeywordRanking)
        .filter(KeywordRanking.location_id == location_id)
        .order_by(KeywordRanking.keyword)
    )
    return result.scalars().all()

async def add_keyword(db: AsyncSession, location_id: UUID, data: KeywordRankingCreate) -> KeywordRanking:
    kw = KeywordRanking(
        location_id=location_id,
        keyword=data.keyword,
        current_rank=data.current_rank,
        search_volume=data.search_volume,
        last_checked_at=datetime.utcnow(),
    )
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw

async def update_keyword_rank(db: AsyncSession, keyword_id: UUID, location_id: UUID, new_rank: int) -> Optional[KeywordRanking]:
    result = await db.execute(
        select(KeywordRanking).filter(KeywordRanking.id == keyword_id, KeywordRanking.location_id == location_id)
    )
    kw = result.scalar_one_or_none()
    if not kw:
        return None
    kw.previous_rank = kw.current_rank
    kw.current_rank = new_rank
    kw.last_checked_at = datetime.utcnow()
    await db.commit()
    await db.refresh(kw)
    return kw

async def delete_keyword(db: AsyncSession, keyword_id: UUID, location_id: UUID) -> bool:
    result = await db.execute(
        select(KeywordRanking).filter(KeywordRanking.id == keyword_id, KeywordRanking.location_id == location_id)
    )
    kw = result.scalar_one_or_none()
    if not kw:
        return False
    await db.delete(kw)
    await db.commit()
    return True

# ── Citation Monitoring ────────────────────────────────────────────────

CITATION_DIRECTORIES = [
    "Yelp", "Foursquare", "YellowPages", "MapQuest",
    "SuperPages", "BBB", "TripAdvisor", "Facebook",
]

async def run_citation_check(db: AsyncSession, location_id: UUID) -> List[CitationRecord]:
    from app.models.tenant import Location
    result = await db.execute(select(Location).filter(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        return []

    records = []
    for directory in CITATION_DIRECTORIES:
        url = f"https://www.{directory.lower().replace(' ', '')}.com"
        issues = []
        consistent = True

        if not location.address:
            issues.append(f"Address not on Google profile — may mismatch on {directory}")
            consistent = False
        if not location.name:
            issues.append(f"Business name not set")
            consistent = False

        record = CitationRecord(
            location_id=location_id,
            directory_name=directory,
            url=url,
            nap_consistent=consistent,
            issues=issues,
            last_checked_at=datetime.utcnow(),
        )
        db.add(record)
        records.append(record)

    await db.commit()
    for r in records:
        await db.refresh(r)
    return records

async def list_citations(db: AsyncSession, location_id: UUID) -> List[CitationRecord]:
    result = await db.execute(
        select(CitationRecord)
        .filter(CitationRecord.location_id == location_id)
        .order_by(CitationRecord.directory_name)
    )
    return result.scalars().all()

async def get_seo_profile(db: AsyncSession, location_id: UUID) -> Optional[SeoProfile]:
    result = await db.execute(select(SeoProfile).filter(SeoProfile.location_id == location_id))
    return result.scalar_one_or_none()

async def update_seo_settings(
    db: AsyncSession, location_id: UUID,
    photo_count: Optional[int] = None, post_count: Optional[int] = None,
) -> Optional[SeoProfile]:
    result = await db.execute(select(SeoProfile).filter(SeoProfile.location_id == location_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = SeoProfile(location_id=location_id)
        db.add(profile)
    if photo_count is not None:
        profile.gbp_photo_count = photo_count
    if post_count is not None:
        profile.gbp_post_count = post_count
    await db.commit()
    await db.refresh(profile)
    return profile

# ── Maps Competitor Visibility ─────────────────────────────────────────

async def get_competitor_maps_rankings(db: AsyncSession, location_id: UUID) -> List[Dict[str, Any]]:
    competitors = await db.execute(
        select(Competitor).filter(Competitor.location_id == location_id)
    )
    comps = competitors.scalars().all()
    results = []
    for comp in comps:
        rankings = await db.execute(
            select(CompetitorMapsRanking)
            .filter(CompetitorMapsRanking.competitor_id == comp.id)
            .order_by(CompetitorMapsRanking.keyword)
        )
        for r in rankings.scalars().all():
            results.append({
                "id": str(r.id),
                "competitor_id": str(comp.id),
                "competitor_name": comp.name,
                "keyword": r.keyword,
                "rank": r.rank,
                "previous_rank": r.previous_rank,
                "last_checked_at": r.last_checked_at,
            })
    return results

async def upsert_maps_ranking(
    db: AsyncSession, competitor_id: UUID, keyword: str, rank: int
) -> CompetitorMapsRanking:
    result = await db.execute(
        select(CompetitorMapsRanking).filter(
            CompetitorMapsRanking.competitor_id == competitor_id,
            CompetitorMapsRanking.keyword == keyword,
        )
    )
    ranking = result.scalar_one_or_none()
    if ranking:
        ranking.previous_rank = ranking.rank
        ranking.rank = rank
        ranking.last_checked_at = datetime.utcnow()
    else:
        ranking = CompetitorMapsRanking(
            competitor_id=competitor_id,
            keyword=keyword,
            rank=rank,
            last_checked_at=datetime.utcnow(),
        )
        db.add(ranking)
    await db.commit()
    await db.refresh(ranking)
    return ranking

async def delete_maps_ranking(db: AsyncSession, ranking_id: UUID) -> bool:
    result = await db.execute(select(CompetitorMapsRanking).filter(CompetitorMapsRanking.id == ranking_id))
    ranking = result.scalar_one_or_none()
    if not ranking:
        return False
    await db.delete(ranking)
    await db.commit()
    return True

# ── GBP Post Scheduler ─────────────────────────────────────────────────

async def list_post_schedules(db: AsyncSession, location_id: UUID) -> List[GbpPostSchedule]:
    result = await db.execute(
        select(GbpPostSchedule)
        .filter(GbpPostSchedule.location_id == location_id)
        .order_by(desc(GbpPostSchedule.scheduled_date))
    )
    return result.scalars().all()

async def create_post_schedule(db: AsyncSession, location_id: UUID, data: GbpPostScheduleCreate) -> GbpPostSchedule:
    post = GbpPostSchedule(
        location_id=location_id,
        content_type=data.content_type,
        title=data.title,
        description=data.description,
        media_url=data.media_url,
        scheduled_date=data.scheduled_date,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post

async def update_post_schedule(db: AsyncSession, post_id: UUID, location_id: UUID, **updates) -> Optional[GbpPostSchedule]:
    result = await db.execute(
        select(GbpPostSchedule).filter(GbpPostSchedule.id == post_id, GbpPostSchedule.location_id == location_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        return None
    for key, value in updates.items():
        if value is not None:
            setattr(post, key, value)
    if updates.get("is_published"):
        post.published_at = datetime.utcnow()
    await db.commit()
    await db.refresh(post)
    return post

async def delete_post_schedule(db: AsyncSession, post_id: UUID, location_id: UUID) -> bool:
    result = await db.execute(
        select(GbpPostSchedule).filter(GbpPostSchedule.id == post_id, GbpPostSchedule.location_id == location_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        return False
    await db.delete(post)
    await db.commit()
    return True

# ── SEO Dashboard (augmented) ──────────────────────────────────────────

async def get_seo_dashboard(db: AsyncSession, location_id: UUID) -> Dict[str, Any]:
    profile = await get_seo_profile(db, location_id)
    keywords = await list_keywords(db, location_id)
    citations = await list_citations(db, location_id)
    maps_rankings = await get_competitor_maps_rankings(db, location_id)
    post_schedules = await list_post_schedules(db, location_id)
    audit = await run_gbp_audit(db, location_id, None) if not profile else None

    return {
        "profile": profile,
        "keywords": keywords,
        "citations": citations,
        "maps_rankings": maps_rankings,
        "post_schedules": post_schedules,
        "audit": audit,
    }
