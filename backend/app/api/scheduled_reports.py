from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sa_delete

from app.database import get_db
from app.models.user import User
from app.models.scheduled_report import ScheduledReport
from app.schemas.scheduled_report import (
    ScheduledReportCreate,
    ScheduledReportUpdate,
    ScheduledReportResponse,
)
from app.core.dependencies import get_current_active_user, verify_client_access, check_location_access

router = APIRouter(prefix="/reports/scheduled", tags=["reports"])


@router.get("", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(ScheduledReport).filter(
        ScheduledReport.agency_id == current_user.agency_id
    ).order_by(ScheduledReport.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ScheduledReportResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_report(
    req: ScheduledReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="User must belong to an agency to schedule reports")

    if req.client_id:
        await verify_client_access(UUID(req.client_id), current_user, db)
    if req.location_id:
        await check_location_access(UUID(req.location_id), current_user, db)

    report = ScheduledReport(
        agency_id=current_user.agency_id,
        client_id=UUID(req.client_id) if req.client_id else None,
        location_id=UUID(req.location_id) if req.location_id else None,
        name=req.name,
        report_type=req.report_type,
        format=req.format,
        cron_expression=req.cron_expression,
        recipients=req.recipients,
        is_active=req.is_active,
        created_by=current_user.id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.patch("/{report_id}", response_model=ScheduledReportResponse)
async def update_scheduled_report(
    report_id: UUID,
    req: ScheduledReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ScheduledReport).filter(
            ScheduledReport.id == report_id,
            ScheduledReport.agency_id == current_user.agency_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    await db.commit()
    await db.refresh(report)
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ScheduledReport).filter(
            ScheduledReport.id == report_id,
            ScheduledReport.agency_id == current_user.agency_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")

    await db.delete(report)
    await db.commit()
