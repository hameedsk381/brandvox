import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.review import Review, ReviewReply
from app.models.tenant import Location, Client
from app.models.integration import GoogleIntegration
from app.models.brand_voice import BrandVoiceProfile, SmartRule
from app.ai.review_reply import generate_reply
from app.services.google_integration_service import publish_google_review_reply

logger = logging.getLogger(__name__)

async def get_brand_voice_for_client(db: AsyncSession, client_id: UUID) -> BrandVoiceProfile:
    result = await db.execute(select(BrandVoiceProfile).filter(BrandVoiceProfile.client_id == client_id))
    profile = result.scalars().first()
    if not profile:
        profile = BrandVoiceProfile(
            client_id=client_id,
            tone="professional",
            greeting_style="Dear [Name],",
            closing_style="Best regards, The [Business] Team",
            personality_traits=["helpful", "professional"]
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile

async def generate_ai_reply_options(db: AsyncSession, review_id: UUID) -> List[Dict[str, Any]]:
    # Load review with hierarchy
    result = await db.execute(
        select(Review)
        .filter(Review.id == review_id)
        .options(selectinload(Review.location).selectinload(Location.client))
    )
    review = result.scalars().first()
    if not review:
        return []
        
    location = review.location
    client = location.client
    
    # Load brand voice
    voice = await get_brand_voice_for_client(db, client.id)
    
    voice_dict = {
        "tone": voice.tone,
        "greeting_style": voice.greeting_style,
        "closing_style": voice.closing_style,
        "vocabulary_notes": voice.vocabulary_notes,
        "personality_traits": voice.personality_traits
    }
    
    # Call AI
    options = await generate_reply(
        review_text=review.text,
        rating=review.rating,
        brand_voice=voice_dict,
        business_name=location.name,
        industry=client.industry,
        author_name=review.author_name
    )
    
    return options

async def save_reply(
    db: AsyncSession,
    review_id: UUID,
    content: str,
    status: str = "posted",
    generated_by: str = "manual",
    approved_by: Optional[UUID] = None
) -> ReviewReply:
    review_res = await db.execute(
        select(Review)
        .filter(Review.id == review_id)
        .options(selectinload(Review.location).selectinload(Location.client).selectinload(Client.agency))
    )
    review = review_res.scalars().first()
    if not review:
        raise ValueError("Review not found")

    if status == "posted" and review.source == "google" and review.location and review.location.google_location_id:
        integration_res = await db.execute(
            select(GoogleIntegration).filter(GoogleIntegration.client_id == review.location.client_id)
        )
        integration = integration_res.scalars().first()
        if not integration:
            raise ValueError("Google account is not connected for this client")

        await publish_google_review_reply(
            db=db,
            agency=review.location.client.agency,
            integration=integration,
            location=review.location,
            source_review_id=review.source_review_id,
            content=content,
        )

        await db.execute(
            update(ReviewReply)
            .where(ReviewReply.review_id == review_id)
            .values(status="replaced")
        )

    reply = ReviewReply(
        review_id=review_id,
        content=content,
        status=status,
        generated_by=generated_by,
        approved_by=approved_by
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)

    return reply


async def approve_reply(db: AsyncSession, reply_id: UUID, approved_by: UUID) -> Optional[ReviewReply]:
    result = await db.execute(
        select(ReviewReply)
        .filter(ReviewReply.id == reply_id)
        .options(
            selectinload(ReviewReply.review)
            .selectinload(Review.location)
            .selectinload(Location.client)
            .selectinload(Client.agency)
        )
    )
    reply = result.scalars().first()
    if not reply:
        return None

    review = reply.review
    if review and review.source == "google" and review.location and review.location.google_location_id:
        integration_res = await db.execute(
            select(GoogleIntegration).filter(GoogleIntegration.client_id == review.location.client_id)
        )
        integration = integration_res.scalars().first()
        if not integration:
            raise ValueError("Google account is not connected for this client")

        await publish_google_review_reply(
            db=db,
            agency=review.location.client.agency,
            integration=integration,
            location=review.location,
            source_review_id=review.source_review_id,
            content=reply.content,
        )

    reply.status = "posted"
    reply.approved_by = approved_by
    await db.execute(
        update(ReviewReply)
        .where(ReviewReply.review_id == reply.review_id)
        .where(ReviewReply.id != reply.id)
        .values(status="replaced")
    )
    await db.commit()
    await db.refresh(reply)
    return reply

async def check_and_apply_smart_rules(db: AsyncSession, review_id: UUID) -> Optional[str]:
    """
    Checks rating, finds active smart rules for location, and automatically replies or drafts.
    """
    result = await db.execute(
        select(Review)
        .filter(Review.id == review_id)
        .options(selectinload(Review.location))
    )
    review = result.scalars().first()
    if not review:
        return None
        
    location = review.location
    
    # Load rules
    rules_result = await db.execute(
        select(SmartRule)
        .filter(SmartRule.location_id == location.id)
        .filter(SmartRule.is_active == True)
    )
    rules = rules_result.scalars().all()
    
    # Find matching rule
    matching_rule = None
    for rule in rules:
        if rule.min_rating <= review.rating <= rule.max_rating:
            matching_rule = rule
            break
            
    if not matching_rule:
        # Default behavior: 4-5 stars auto_reply, 3 stars approval, 1-2 stars escalate
        if review.rating >= 4:
            action = "auto_reply"
        elif review.rating == 3:
            action = "approval_required"
        else:
            action = "escalate"
    else:
        action = matching_rule.action
        
    logger.info(f"Applying rule action '{action}' for review rating {review.rating}")
    
    # Execute action
    if action == "auto_reply":
        # Generate reply and post
        options = await generate_ai_reply_options(db, review_id)
        if options:
            reply_text = options[0]["content"]
            await save_reply(
                db=db,
                review_id=review_id,
                content=reply_text,
                status="posted",
                generated_by="ai"
            )
            return "auto_reply"
    elif action == "approval_required" or action == "escalate":
        # Generate replies and save as drafts
        options = await generate_ai_reply_options(db, review_id)
        for opt in options:
            await save_reply(
                db=db,
                review_id=review_id,
                content=opt["content"],
                status="draft",
                generated_by="ai"
            )
        return "draft"
    
    return "manual"
