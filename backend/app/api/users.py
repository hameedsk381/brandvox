from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.schemas.auth import UserResponse, RegisterRequest, ExportDataResponse
from app.models.user import User
from app.models.review import Review, ReviewReply
from app.models.chat import ChatSession, ChatMessage
from app.models.audit import AuditLog
from app.core.dependencies import get_current_active_user, RoleChecker
from app.core.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    query = select(User)
    if current_user.role != "super_admin":
        if current_user.agency_id:
            query = query.filter(User.agency_id == current_user.agency_id)
        elif current_user.client_id:
            query = query.filter(User.client_id == current_user.client_id)
        else:
            return [current_user]
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=UserResponse)
async def create_user(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    result = await db.execute(select(User).filter(User.email == req.email))
    exist = result.scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="User email already exists")
    role = "read_only"
    if current_user.role == "agency_admin":
        role = "client_admin"
    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        name=req.name,
        role=role,
        agency_id=current_user.agency_id,
        client_id=current_user.client_id,
        location_id=current_user.location_id,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/me/export", response_model=ExportDataResponse)
async def export_my_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    reviews = await db.execute(
        select(Review).filter(Review.author_name == current_user.name)
    )
    reviews_data = [{"id": str(r.id), "text": r.text, "rating": r.rating, "source": r.source, "review_date": str(r.review_date)} for r in reviews.scalars().all()]

    replies = await db.execute(
        select(ReviewReply).filter(ReviewReply.approved_by == current_user.id)
    )
    replies_data = [{"id": str(r.id), "content": r.content, "status": r.status} for r in replies.scalars().all()]

    sessions = await db.execute(
        select(ChatSession).filter(ChatSession.user_id == current_user.id)
    )
    sessions_data = []
    for s in sessions.scalars().all():
        msgs = await db.execute(
            select(ChatMessage).filter(ChatMessage.session_id == s.id)
        )
        sessions_data.append({
            "id": str(s.id),
            "created_at": str(s.created_at),
            "messages": [{"role": m.role, "content": m.content} for m in msgs.scalars().all()],
        })

    logs = await db.execute(
        select(AuditLog).filter(AuditLog.user_id == current_user.id)
    )
    logs_data = [{"action": l.action, "resource_type": l.resource_type, "ip_address": l.ip_address, "created_at": str(l.created_at)} for l in logs.scalars().all()]

    return {
        "user": current_user,
        "data": {
            "account": {
                "email": current_user.email,
                "name": current_user.name,
                "role": current_user.role,
                "created_at": str(current_user.created_at),
            },
            "reviews": reviews_data,
            "review_replies": replies_data,
            "chat_sessions": sessions_data,
            "audit_logs": logs_data,
        },
    }

@router.delete("/me", status_code=204)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.is_active = False
    current_user.email = f"deleted-{current_user.id}@anon.reputationos.ai"
    current_user.name = "Deleted User"
    await db.commit()
