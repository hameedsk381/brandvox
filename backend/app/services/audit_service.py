from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Request
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        agency_id: str | UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str | UUID] = None,
        details: Dict[str, Any] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log an audit event.
        """
        ip_address = None
        if request:
            # Try to get IP from standard headers if behind a proxy
            x_forwarded_for = request.headers.get("x-forwarded-for")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            elif request.client:
                ip_address = request.client.host
                
        audit_log = AuditLog(
            agency_id=agency_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        return audit_log

audit_service = AuditService()
