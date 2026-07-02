from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.core.dependencies import get_current_active_user, RoleChecker

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["agency_admin"]))
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User is not part of an agency")

    # Build query
    stmt = select(
        AuditLog, User.name.label('user_name'), User.email.label('user_email')
    ).outerjoin(
        User, AuditLog.user_id == User.id
    ).filter(
        AuditLog.agency_id == current_user.agency_id
    )

    if action:
        stmt = stmt.filter(AuditLog.action == action)
    if user_id:
        stmt = stmt.filter(AuditLog.user_id == user_id)
    if resource_type:
        stmt = stmt.filter(AuditLog.resource_type == resource_type)

    stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()
    
    # Map raw rows to pydantic response (incorporating user_name/user_email)
    response = []
    for row in rows:
        log = row.AuditLog
        response.append(
            AuditLogResponse(
                id=log.id,
                agency_id=log.agency_id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at,
                user_name=row.user_name,
                user_email=row.user_email
            )
        )
        
    return response
