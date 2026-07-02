from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class ReviewReplyCreate(BaseModel):
    content: str
    generated_by: str = "manual"

class ReviewReplyResponse(BaseModel):
    id: UUID
    review_id: UUID
    content: str
    status: str
    generated_by: str
    approved_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SentimentResultResponse(BaseModel):
    sentiment: str
    confidence: float
    emotions: List[str]

    class Config:
        from_attributes = True

class TopicResultResponse(BaseModel):
    topic: str
    sub_topic: Optional[str] = None
    sentiment: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    location_id: UUID
    source: str = "google"
    source_review_id: str
    author_name: Optional[str] = None
    author_image_url: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = None
    review_date: datetime

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: UUID
    created_at: datetime
    sentiment_result: Optional[SentimentResultResponse] = None
    topic_results: List[TopicResultResponse] = []
    replies: List[ReviewReplyResponse] = []

    class Config:
        from_attributes = True

class ReviewsListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    pages: int
