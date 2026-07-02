from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.database import get_db
from app.schemas.review import ReviewsListResponse, ReviewResponse, ReviewCreate
from app.services.review_service import get_reviews, get_review_by_id, create_review
from app.services.sentiment_service import analyze_review_sentiment_and_topics
from app.services.reply_service import check_and_apply_smart_rules
from app.services.alert_service import detect_crisis
from app.models.user import User
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.get("", response_model=ReviewsListResponse)
async def list_reviews(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    rating: Optional[int] = Query(default=None, ge=1, le=5),
    sentiment: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Pass scopes based on user role
    agency_id = current_user.agency_id if current_user.role != "super_admin" else None
    client_id = current_user.client_id if current_user.role not in ["super_admin", "agency_admin"] else None
    location_id = current_user.location_id if current_user.role in ["customer_support", "branch_manager"] else None

    result = await get_reviews(
        db=db,
        agency_id=agency_id,
        client_id=client_id,
        location_id=location_id,
        rating=rating,
        sentiment=sentiment,
        source=source,
        search=search,
        page=page,
        size=size
    )
    return result

@router.get("/{id}", response_model=ReviewResponse)
async def get_review(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    review = await get_review_by_id(db, id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.post("", response_model=ReviewResponse)
async def add_manual_review(
    req: ReviewCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    # Create the review
    review = await create_review(db, req)
    
    # Process AI async in background
    async def process_pipeline(review_id: UUID):
        # We need a new session context since background task runs after request completes
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as bg_db:
            # 1. Analyze sentiment & topics
            await analyze_review_sentiment_and_topics(bg_db, review_id)
            # 2. Check and apply automation reply rules
            await check_and_apply_smart_rules(bg_db, review_id)
            # 3. Detect and dispatch crisis alerts
            await detect_crisis(bg_db, review_id)
            
    background_tasks.add_task(process_pipeline, review.id)
    
    return review
