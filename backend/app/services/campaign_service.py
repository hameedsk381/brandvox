import io
import base64
import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from app.models.campaign import ReviewCampaign, CampaignContact, EmployeeLeaderboard
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignContactCreate
from app.services.notification_service import (
    send_sms, send_email, send_whatsapp,
    build_review_request_message, build_review_request_email,
)

logger = logging.getLogger(__name__)

async def list_campaigns(db: AsyncSession, agency_id: UUID) -> List[ReviewCampaign]:
    result = await db.execute(
        select(ReviewCampaign)
        .filter(ReviewCampaign.agency_id == agency_id)
        .order_by(desc(ReviewCampaign.created_at))
    )
    return result.scalars().all()

async def get_campaign(db: AsyncSession, campaign_id: UUID, agency_id: UUID) -> Optional[ReviewCampaign]:
    result = await db.execute(
        select(ReviewCampaign)
        .filter(ReviewCampaign.id == campaign_id, ReviewCampaign.agency_id == agency_id)
    )
    return result.scalar_one_or_none()

async def create_campaign(db: AsyncSession, agency_id: UUID, data: CampaignCreate) -> ReviewCampaign:
    campaign = ReviewCampaign(
        agency_id=agency_id,
        name=data.name,
        campaign_type=data.campaign_type,
        target_url=data.target_url,
        redirect_url=data.redirect_url,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign

async def update_campaign(db: AsyncSession, campaign_id: UUID, agency_id: UUID, data: CampaignUpdate) -> Optional[ReviewCampaign]:
    campaign = await get_campaign(db, campaign_id, agency_id)
    if not campaign:
        return None
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    for key, value in updates.items():
        setattr(campaign, key, value)
    await db.commit()
    await db.refresh(campaign)
    return campaign

async def delete_campaign(db: AsyncSession, campaign_id: UUID, agency_id: UUID) -> bool:
    campaign = await get_campaign(db, campaign_id, agency_id)
    if not campaign:
        return False
    await db.delete(campaign)
    await db.commit()
    return True

async def get_campaign_analytics(db: AsyncSession, campaign_id: UUID, agency_id: UUID) -> Optional[Dict[str, Any]]:
    campaign = await get_campaign(db, campaign_id, agency_id)
    if not campaign:
        return None
    result = await db.execute(
        select(func.count()).select_from(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id)
    )
    total_contacts = result.scalar() or 0

    sent_result = await db.execute(
        select(func.count()).select_from(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id, CampaignContact.status != "pending")
    )
    sent_count = sent_result.scalar() or 0

    opened_result = await db.execute(
        select(func.count()).select_from(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "opened")
    )
    opened_count = opened_result.scalar() or 0

    converted_result = await db.execute(
        select(func.count()).select_from(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "converted")
    )
    converted_count = converted_result.scalar() or 0

    return {
        "campaign": campaign,
        "total_contacts": total_contacts,
        "sent_count": sent_count,
        "opened_count": opened_count,
        "converted_count": converted_count,
        "open_rate": round((opened_count / sent_count * 100) if sent_count > 0 else 0, 1),
        "conversion_rate": round((converted_count / sent_count * 100) if sent_count > 0 else 0, 1),
    }

async def generate_qr_code(campaign: ReviewCampaign) -> str:
    try:
        import qrcode
        target = campaign.target_url or "https://google.com"
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        logger.warning("qrcode library not available")
        return ""

async def add_campaign_contacts(db: AsyncSession, campaign_id: UUID, contacts: List[CampaignContactCreate]) -> List[CampaignContact]:
    created = []
    for c in contacts:
        contact = CampaignContact(
            campaign_id=campaign_id,
            recipient=c.recipient,
            channel=c.channel,
            employee_name=c.employee_name,
        )
        db.add(contact)
        created.append(contact)
    await db.commit()
    for c in created:
        await db.refresh(c)
    return created

async def list_contacts(db: AsyncSession, campaign_id: UUID) -> List[CampaignContact]:
    result = await db.execute(
        select(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id)
        .order_by(desc(CampaignContact.created_at))
    )
    return result.scalars().all()

async def send_campaign_contacts(db: AsyncSession, campaign_id: UUID, agency_id: UUID) -> Dict[str, Any]:
    campaign = await get_campaign(db, campaign_id, agency_id)
    if not campaign:
        return {"success": False, "error": "Campaign not found"}

    result = await db.execute(
        select(CampaignContact)
        .filter(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "pending")
    )
    contacts = result.scalars().all()
    if not contacts:
        return {"success": True, "sent": 0, "message": "No pending contacts"}

    target_url = campaign.target_url or "https://g.page/r/CvFnP4d4M2r7EBM/review"
    message = build_review_request_message("our business", target_url)
    email_html = build_review_request_email("our business", target_url)

    sent = 0
    failed = 0
    for contact in contacts:
        success = False
        if contact.channel == "sms":
            success = await send_sms(contact.recipient, message)
        elif contact.channel == "email":
            success = await send_email(contact.recipient, "We'd love your feedback!", email_html)
        elif contact.channel == "whatsapp":
            success = await send_whatsapp(contact.recipient, message)

        if success:
            contact.status = "sent"
            contact.sent_at = datetime.utcnow()
            sent += 1
        else:
            failed += 1

    campaign.total_sent += sent
    await db.commit()
    return {"success": True, "sent": sent, "failed": failed}

# ── Employee Leaderboard ──────────────────────────────────────────────

async def get_leaderboard(db: AsyncSession, agency_id: UUID, location_id: Optional[UUID] = None, days: int = 30) -> List[Dict[str, Any]]:
    query = select(
        CampaignContact.employee_name,
        func.count(CampaignContact.id).label("total"),
        func.sum(CampaignContact.status == "converted").label("conversions"),
    ).select_from(CampaignContact).join(
        ReviewCampaign, CampaignContact.campaign_id == ReviewCampaign.id
    ).filter(
        ReviewCampaign.agency_id == agency_id,
        CampaignContact.employee_name.isnot(None),
        CampaignContact.created_at >= datetime.utcnow() - timedelta(days=days),
    )

    if location_id:
        query = query.filter(ReviewCampaign.location_id == location_id)

    query = query.group_by(CampaignContact.employee_name).order_by(desc("total"))
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "employee_name": row[0],
            "requests_sent": row[1],
            "conversions": row[2] or 0,
            "conversion_rate": round(((row[2] or 0) / row[1] * 100), 1) if row[1] > 0 else 0,
        }
        for row in rows
    ]

async def record_employee_conversion(db: AsyncSession, contact_id: UUID) -> bool:
    result = await db.execute(select(CampaignContact).filter(CampaignContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        return False
    contact.status = "converted"
    contact.converted_at = datetime.utcnow()
    if contact.employee_name:
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = period_start.replace(month=period_start.month + 1) if period_start.month < 12 else period_start.replace(year=period_start.year + 1, month=1)
        period_end = next_month - timedelta(seconds=1)

        existing = await db.execute(
            select(EmployeeLeaderboard).filter(
                EmployeeLeaderboard.employee_name == contact.employee_name,
                EmployeeLeaderboard.agency_id == contact.campaign.agency_id,
                EmployeeLeaderboard.period_start == period_start,
            )
        )
        entry = existing.scalar_one_or_none()
        if entry:
            entry.reviews_generated += 1
        else:
            entry = EmployeeLeaderboard(
                agency_id=contact.campaign.agency_id,
                employee_name=contact.employee_name,
                reviews_generated=1,
                period_start=period_start,
                period_end=period_end,
            )
            db.add(entry)
    await db.commit()
    return True

# ── Aggregated Dashboard ──────────────────────────────────────────────

async def get_generation_dashboard(db: AsyncSession, agency_id: UUID) -> Dict[str, Any]:
    total_campaigns = await db.execute(
        select(func.count()).select_from(ReviewCampaign)
        .filter(ReviewCampaign.agency_id == agency_id)
    )

    total_sent = await db.execute(
        select(func.coalesce(func.sum(ReviewCampaign.total_sent), 0))
        .filter(ReviewCampaign.agency_id == agency_id)
    )

    total_converted = await db.execute(
        select(func.coalesce(func.sum(ReviewCampaign.total_converted), 0))
        .filter(ReviewCampaign.agency_id == agency_id)
    )

    active_campaigns = await db.execute(
        select(func.count()).select_from(ReviewCampaign)
        .filter(ReviewCampaign.agency_id == agency_id, ReviewCampaign.is_active == True)
    )

    campaigns_list = await db.execute(
        select(ReviewCampaign)
        .filter(ReviewCampaign.agency_id == agency_id)
        .order_by(desc(ReviewCampaign.created_at))
    )
    campaigns = campaigns_list.scalars().all()

    tc = total_campaigns.scalar() or 0
    ts = total_sent.scalar() or 0
    tconv = total_converted.scalar() or 0
    ac = active_campaigns.scalar() or 0

    return {
        "total_campaigns": tc,
        "total_sent": ts,
        "total_converted": tconv,
        "active_campaigns": ac,
        "conversion_rate": round((tconv / ts * 100) if ts > 0 else 0, 1),
        "recent_campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "campaign_type": c.campaign_type,
                "total_sent": c.total_sent,
                "total_converted": c.total_converted,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns[:5]
        ],
    }
