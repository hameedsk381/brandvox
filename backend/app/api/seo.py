from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.database import get_db
from typing import Optional as OptType
from app.schemas.seo import (
    SeoProfileResponse, KeywordRankingCreate, KeywordRankingResponse,
    CitationRecordResponse, SeoAuditResult, SeoDashboardData,
    CompetitorMapsRankingResponse, GbpPostScheduleCreate, GbpPostScheduleResponse,
)
from app.services.seo_service import (
    run_gbp_audit, get_seo_profile, list_keywords, add_keyword,
    update_keyword_rank, delete_keyword, list_citations,
    run_citation_check, update_seo_settings, get_seo_dashboard,
    get_competitor_maps_rankings, upsert_maps_ranking, delete_maps_ranking,
    list_post_schedules, create_post_schedule, update_post_schedule, delete_post_schedule,
)
from app.models.user import User
from app.core.dependencies import get_current_active_user, check_location_access

router = APIRouter(prefix="/seo", tags=["seo"])

@router.get("/audit", response_model=SeoAuditResult)
async def audit_location(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    result = await run_gbp_audit(db, location_id, current_user.agency_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/dashboard", response_model=SeoDashboardData)
async def seo_dashboard(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await get_seo_dashboard(db, location_id)

@router.get("/profile", response_model=Optional[SeoProfileResponse])
async def get_profile(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    profile = await get_seo_profile(db, location_id)
    if not profile:
        result = await run_gbp_audit(db, location_id, current_user.agency_id)
        if "error" not in result:
            profile = await get_seo_profile(db, location_id)
    return profile

@router.patch("/profile", response_model=SeoProfileResponse)
async def update_profile(
    location_id: UUID = Query(...),
    photo_count: Optional[int] = Query(default=None),
    post_count: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    profile = await update_seo_settings(db, location_id, photo_count, post_count)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/keywords", response_model=List[KeywordRankingResponse])
async def get_keywords(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await list_keywords(db, location_id)

@router.post("/keywords", response_model=KeywordRankingResponse, status_code=201)
async def create_keyword(
    location_id: UUID = Query(...),
    req: KeywordRankingCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await add_keyword(db, location_id, req)

@router.patch("/keywords/{keyword_id}", response_model=KeywordRankingResponse)
async def update_keyword(
    keyword_id: UUID,
    location_id: UUID = Query(...),
    current_rank: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    kw = await update_keyword_rank(db, keyword_id, location_id, current_rank)
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return kw

@router.delete("/keywords/{keyword_id}", status_code=204)
async def remove_keyword(
    keyword_id: UUID,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    deleted = await delete_keyword(db, keyword_id, location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Keyword not found")

@router.get("/citations", response_model=List[CitationRecordResponse])
async def get_citations(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await list_citations(db, location_id)

@router.post("/citations/check", response_model=List[CitationRecordResponse])
async def check_citations(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await run_citation_check(db, location_id)

# ── Maps Competitor Visibility ─────────────────────────────────────────

@router.get("/maps-rankings", response_model=List[CompetitorMapsRankingResponse])
async def get_maps_rankings(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await get_competitor_maps_rankings(db, location_id)

@router.post("/maps-rankings", response_model=CompetitorMapsRankingResponse)
async def create_maps_ranking(
    competitor_id: UUID = Query(...),
    keyword: str = Query(...),
    rank: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.models.competitor import Competitor
    result = await db.execute(select(Competitor).filter(Competitor.id == competitor_id))
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")
    await check_location_access(comp.location_id, current_user, db)
    ranking = await upsert_maps_ranking(db, competitor_id, keyword, rank)
    cmp_res = await db.execute(select(Competitor).filter(Competitor.id == competitor_id))
    comp = cmp_res.scalar_one()
    return {
        "id": str(ranking.id),
        "competitor_id": str(comp.id),
        "competitor_name": comp.name,
        "keyword": ranking.keyword,
        "rank": ranking.rank,
        "previous_rank": ranking.previous_rank,
        "last_checked_at": ranking.last_checked_at,
    }

@router.delete("/maps-rankings/{ranking_id}", status_code=204)
async def remove_maps_ranking(
    ranking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    deleted = await delete_maps_ranking(db, ranking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ranking not found")

# ── GBP Post Scheduler ─────────────────────────────────────────────────

@router.get("/posts", response_model=List[GbpPostScheduleResponse])
async def get_posts(
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await list_post_schedules(db, location_id)

@router.post("/posts", response_model=GbpPostScheduleResponse, status_code=201)
async def add_post(
    location_id: UUID = Query(...),
    req: GbpPostScheduleCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    return await create_post_schedule(db, location_id, req)

@router.patch("/posts/{post_id}", response_model=GbpPostScheduleResponse)
async def edit_post(
    post_id: UUID,
    location_id: UUID = Query(...),
    title: OptType[str] = Query(default=None),
    description: OptType[str] = Query(default=None),
    media_url: OptType[str] = Query(default=None),
    scheduled_date: OptType[str] = Query(default=None),
    is_published: OptType[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    updates = {k: v for k, v in {"title": title, "description": description, "media_url": media_url, "is_published": is_published}.items() if v is not None}
    if scheduled_date:
        from datetime import datetime
        updates["scheduled_date"] = datetime.fromisoformat(scheduled_date.replace("Z", "+00:00"))
    post = await update_post_schedule(db, post_id, location_id, **updates)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.delete("/posts/{post_id}", status_code=204)
async def remove_post(
    post_id: UUID,
    location_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await check_location_access(location_id, current_user, db)
    deleted = await delete_post_schedule(db, post_id, location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found")
