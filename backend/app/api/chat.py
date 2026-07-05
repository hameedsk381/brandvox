from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from uuid import UUID

from app.database import get_db
from app.core.dependencies import get_current_active_user, check_location_access
from app.models.user import User
from app.models.chat import ChatSession, SessionType
from app.ai.agent import run_chat_agent

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    location_id: Optional[str] = None
    location_name: Optional[str] = None

@router.post("/manager")
async def chat_manager(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if request.location_id:
        try:
            location_uuid = UUID(request.location_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid location ID")
        await check_location_access(location_uuid, current_user, db)

    if request.session_id:
        stmt = select(ChatSession).where(ChatSession.id == request.session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = ChatSession(
            session_type=SessionType.manager,
            user_id=str(current_user.id) if current_user.id else None,
            client_id=str(current_user.client_id) if current_user.client_id else None
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
    # Return StreamingResponse
    # We yield the session ID first so the client knows it, then the stream
    async def event_generator():
        yield f'{{"type": "session_id", "session_id": "{session.id}"}}\n'
        async for chunk in run_chat_agent(session, db, request.message, request.location_id, request.location_name):
            yield chunk + "\n"
            
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.post("/widget/{client_id}")
async def chat_widget(
    client_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # Public endpoint, no auth required, but scoped to client_id
    if request.session_id:
        stmt = select(ChatSession).where(ChatSession.id == request.session_id, ChatSession.client_id == client_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = ChatSession(
            session_type=SessionType.customer,
            client_id=client_id
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
    async def event_generator():
        yield f'{{"type": "session_id", "session_id": "{session.id}"}}\n'
        async for chunk in run_chat_agent(session, db, request.message):
            yield chunk + "\n"
            
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
