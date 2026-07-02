import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.review import Review
from app.models.sentiment import SentimentResult, TopicResult
from app.ai.sentiment import analyze_sentiment
from app.ai.topic_extraction import extract_topics

logger = logging.getLogger(__name__)

async def analyze_review_sentiment_and_topics(db: AsyncSession, review_id: UUID) -> bool:
    try:
        # Load review
        result = await db.execute(select(Review).filter(Review.id == review_id))
        review = result.scalars().first()
        if not review:
            logger.error(f"Review {review_id} not found for sentiment analysis")
            return False
            
        # 1. Sentiment analysis
        sentiment_data = await analyze_sentiment(review.text)
        
        # Check if already exists (avoid duplicates)
        exist_sent_result = await db.execute(select(SentimentResult).filter(SentimentResult.review_id == review_id))
        exist_sent = exist_sent_result.scalars().first()
        
        if exist_sent:
            exist_sent.sentiment = sentiment_data["sentiment"]
            exist_sent.confidence = sentiment_data["confidence"]
            exist_sent.emotions = sentiment_data["emotions"]
        else:
            db_sentiment = SentimentResult(
                review_id=review_id,
                sentiment=sentiment_data["sentiment"],
                confidence=sentiment_data["confidence"],
                emotions=sentiment_data["emotions"]
            )
            db.add(db_sentiment)
            
        # 2. Topic extraction
        topics_data = await extract_topics(review.text)
        
        # Clear existing topics for this review first
        await db.execute(select(TopicResult).filter(TopicResult.review_id == review_id))
        # (SQLite/Postgres deletion logic)
        from sqlalchemy import delete
        await db.execute(delete(TopicResult).where(TopicResult.review_id == review_id))
        
        # Save new topics
        for topic in topics_data:
            db_topic = TopicResult(
                review_id=review_id,
                topic=topic["topic"],
                sub_topic=topic.get("sub_topic"),
                sentiment=topic.get("sentiment")
            )
            db.add(db_topic)
            
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error in analyze_review_sentiment_and_topics: {e}")
        await db.rollback()
        return False
