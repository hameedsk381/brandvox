from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
from app.database import get_db
from app.services.report_service import generate_excel_report, generate_pdf_report, generate_pptx_report
from app.models.user import User
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate")
async def generate_report(
    format: str = Query(default="pdf"), # pdf or excel
    report_type: str = Query(default="monthly"), # weekly, monthly, quarterly
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agency_id = current_user.agency_id if current_user.role != "super_admin" else None
    client_id = current_user.client_id if current_user.role not in ["super_admin", "agency_admin"] else None
    location_id = current_user.location_id if current_user.role in ["customer_support", "branch_manager"] else None

    if format == "excel":
        file_bytes = await generate_excel_report(
            db=db,
            agency_id=agency_id,
            client_id=client_id,
            location_id=location_id,
            report_type=report_type
        )
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reputation_report_{report_type}.xlsx"}
        )
    elif format == "pptx":
        file_bytes = await generate_pptx_report(
            db=db,
            agency_id=agency_id,
            client_id=client_id,
            location_id=location_id,
            report_type=report_type
        )
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename=reputation_report_{report_type}.pptx"}
        )
    else: # pdf
        file_bytes = await generate_pdf_report(
            db=db,
            agency_id=agency_id,
            client_id=client_id,
            location_id=location_id,
            report_type=report_type
        )
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reputation_report_{report_type}.pdf"}
        )
