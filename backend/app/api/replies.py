from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.models.review import ReviewReply
from app.schemas.review import ReviewReplyResponse, ReviewReplyCreate
from app.services.reply_service import approve_reply, generate_ai_reply_options, save_reply
from app.services.audit_service import audit_service
from app.models.user import User
from app.core.dependencies import RoleChecker

router = APIRouter(tags=["replies"])

@router.post("/reviews/{id}/generate-reply")
async def generate_ai_replies(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["customer_support"]))
):
    options = await generate_ai_reply_options(db, id)
    if not options:
        # If Groq client returns empty, we throw error
        raise HTTPException(status_code=500, detail="Could not generate reply choices at this time.")
    return {"replies": options}

@router.post("/reviews/{id}/reply", response_model=ReviewReplyResponse)
async def submit_reply(
    id: UUID,
    req: ReviewReplyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["customer_support"]))
):
    status = "posted"
    try:
        reply = await save_reply(
            db=db,
            review_id=id,
            content=req.content,
            status=status,
            generated_by=req.generated_by,
            approved_by=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return reply
    
    
@router.patch("/replies/{id}/approve", response_model=ReviewReplyResponse)
async def approve_reply_draft(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    try:
        reply = await approve_reply(db, id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not reply:
        raise HTTPException(status_code=404, detail="Reply draft not found")

    if current_user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=current_user.agency_id,
            action="reply.approved",
            resource_type="ReviewReply",
            resource_id=str(reply.id),
            user_id=current_user.id,
            request=request
        )

    return reply

@router.patch("/replies/{id}/reject", response_model=ReviewReplyResponse)
async def reject_reply_draft(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["marketing_manager"]))
):
    result = await db.execute(
        update(ReviewReply)
        .where(ReviewReply.id == id)
        .values(status="rejected")
        .returning(ReviewReply)
    )
    reply = result.scalars().first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply draft not found")
        
    if current_user.agency_id:
        await audit_service.log_action(
            db=db,
            agency_id=current_user.agency_id,
            action="reply.rejected",
            resource_type="ReviewReply",
            resource_id=str(reply.id),
            user_id=current_user.id,
            request=request
        )
        
    await db.commit()
    return reply
