from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from app.models.review import Review, ReviewReply
from app.models.sentiment import SentimentResult
from app.models.tenant import Location, Client
from app.schemas.review import ReviewCreate, ReviewReplyCreate

async def get_reviews(
    db: AsyncSession,
    agency_id: Optional[UUID] = None,
    client_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    rating: Optional[int] = None,
    sentiment: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20
) -> Dict[str, Any]:
    # Build query
    query = select(Review).options(
        selectinload(Review.sentiment_result),
        selectinload(Review.topic_results),
        selectinload(Review.replies).selectinload(ReviewReply.approved_by_user)
    )
    
    # Filter by hierarchy
    if location_id:
        query = query.filter(Review.location_id == location_id)
    elif client_id:
        query = query.join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        query = query.join(Location).join(Client).filter(Client.agency_id == agency_id)
        
    # Additional filters
    if rating:
        query = query.filter(Review.rating == rating)
        
    if sentiment:
        # Join sentiment
        query = query.join(SentimentResult).filter(SentimentResult.sentiment == sentiment)
        
    if source:
        query = query.filter(Review.source == source)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Review.text.ilike(search_filter),
                Review.author_name.ilike(search_filter)
            )
        )
        
    # Total count query (clone filters)
    count_query = select(func.count(Review.id))
    if location_id:
        count_query = count_query.filter(Review.location_id == location_id)
    elif client_id:
        count_query = count_query.join(Location).filter(Location.client_id == client_id)
    elif agency_id:
        count_query = count_query.join(Location).join(Client).filter(Client.agency_id == agency_id)
        
    if rating:
        count_query = count_query.filter(Review.rating == rating)
    if sentiment:
        count_query = count_query.join(SentimentResult).filter(SentimentResult.sentiment == sentiment)
    if source:
        count_query = count_query.filter(Review.source == source)
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.filter(
            or_(
                Review.text.ilike(search_filter),
                Review.author_name.ilike(search_filter)
            )
        )

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination and sorting
    query = query.order_by(desc(Review.review_date)).offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }

async def get_review_by_id(db: AsyncSession, review_id: UUID) -> Optional[Review]:
    query = select(Review).filter(Review.id == review_id).options(
        selectinload(Review.sentiment_result),
        selectinload(Review.topic_results),
        selectinload(Review.replies).selectinload(ReviewReply.approved_by_user)
    )
    result = await db.execute(query)
    return result.scalars().first()

async def create_review(db: AsyncSession, req: ReviewCreate) -> Review:
    review = Review(
        location_id=req.location_id,
        source=req.source,
        source_review_id=req.source_review_id,
        author_name=req.author_name,
        author_image_url=req.author_image_url,
        rating=req.rating,
        text=req.text,
        review_date=req.review_date
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review
