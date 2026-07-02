import json
import logging
from uuid import UUID
from typing import List, Optional
import httpx
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.alert import CrisisAlert, AlertIntegration, AlertSeverity, AlertCategory, AlertStatus, IntegrationType
from app.models.review import Review
from app.models.tenant import Location
from app.ai.groq_client import get_groq_client

logger = logging.getLogger(__name__)

# Fallback heuristic keywords
CRISIS_KEYWORDS = {
    AlertCategory.health_safety: ["food poisoning", "hospital", "sick", "roach", "rat", "glass in food", "raw chicken"],
    AlertCategory.legal: ["sue", "sued", "lawyer", "lawsuit", "illegal", "attorney", "court"],
    AlertCategory.pr_crisis: ["racist", "assault", "harass", "discriminate", "scam", "police", "fraud"],
    AlertCategory.spam: ["bitcoin", "crypto", "forex", "invest", "click here", "buy followers"],
    AlertCategory.fake_review: ["bot", "fake review", "paid review", "never been here"]
}

async def _heuristic_fallback(text: str) -> Optional[dict]:
    if not text:
        return None
    
    text_lower = text.lower()
    detected_category = None
    
    for category, keywords in CRISIS_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected_category = category
            break
            
    if detected_category:
        severity = AlertSeverity.critical if detected_category in [AlertCategory.health_safety, AlertCategory.legal, AlertCategory.pr_crisis] else AlertSeverity.medium
        return {
            "is_crisis": True,
            "category": detected_category.value,
            "severity": severity.value,
            "analysis_reason": f"Heuristic matched keywords for {detected_category.value}"
        }
    return {"is_crisis": False}

async def detect_crisis(db: AsyncSession, review_id: UUID) -> Optional[CrisisAlert]:
    # Get review
    result = await db.execute(select(Review).filter(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review or not review.text:
        return None
        
    groq = get_groq_client()
    system_prompt = (
        "You are an AI Crisis Detection Agent. Analyze the following customer review and determine if it represents a PR crisis, legal threat, health & safety violation, spam, or a fake review. "
        "Return a JSON object with exactly these fields:\n"
        "- is_crisis: boolean\n"
        "- category: string (one of: 'pr_crisis', 'health_safety', 'legal', 'spam', 'fake_review')\n"
        "- severity: string (one of: 'critical', 'high', 'medium')\n"
        "- analysis_reason: string (brief explanation)"
    )
    
    analysis_data = None
    if groq.client:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review Text: {review.text}"}
        ]
        completion = await groq.chat_completion(messages, temperature=0.1, response_json=True)
        if completion:
            try:
                cleaned = completion.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                analysis_data = json.loads(cleaned)
            except Exception as e:
                logger.error(f"Failed to parse crisis detection JSON: {e}")
                
    if not analysis_data:
        analysis_data = await _heuristic_fallback(review.text)
        
    if analysis_data and analysis_data.get("is_crisis"):
        try:
            category_val = AlertCategory(analysis_data.get("category", "pr_crisis"))
            severity_val = AlertSeverity(analysis_data.get("severity", "high"))
            
            alert = CrisisAlert(
                location_id=review.location_id,
                review_id=review.id,
                severity=severity_val,
                category=category_val,
                analysis_reason=analysis_data.get("analysis_reason", "AI detected crisis anomaly.")
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            
            # Dispatch webhook in background
            await dispatch_alert(db, alert, review)
            
            return alert
        except ValueError as e:
            logger.error(f"Invalid alert data: {e}")
            
    return None

async def dispatch_alert(db: AsyncSession, alert: CrisisAlert, review: Review):
    # Fetch integrations
    result = await db.execute(select(AlertIntegration).filter(
        AlertIntegration.location_id == alert.location_id,
        AlertIntegration.is_active == True
    ))
    integrations = result.scalars().all()
    
    if not integrations:
        return
        
    # Get location name
    loc_res = await db.execute(select(Location).filter(Location.id == alert.location_id))
    location = loc_res.scalar_one_or_none()
    loc_name = location.name if location else "Unknown Location"
    
    message_title = f"🚨 CRISIS ALERT: {alert.severity.value.upper()} Severity ({alert.category.value})"
    message_body = (
        f"*Location:* {loc_name}\n"
        f"*Reviewer:* {review.author_name}\n"
        f"*Rating:* {review.rating} Stars\n"
        f"*Review:* \"{review.text}\"\n\n"
        f"*AI Analysis:* {alert.analysis_reason}"
    )

    async with httpx.AsyncClient() as client:
        for integration in integrations:
            payload = {}
            if integration.type == IntegrationType.slack:
                payload = {
                    "text": f"{message_title}\n{message_body}"
                }
            elif integration.type == IntegrationType.teams:
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF0000" if alert.severity == AlertSeverity.critical else "FFA500",
                    "summary": message_title,
                    "sections": [{
                        "activityTitle": message_title,
                        "text": message_body.replace("\n", "\n\n")
                    }]
                }
            elif integration.type == IntegrationType.email:
                # Mock email send logic
                logger.info(f"Simulating email dispatch to {integration.webhook_url} for Alert {alert.id}")
                continue
                
            try:
                await client.post(str(integration.webhook_url), json=payload, timeout=5.0)
                logger.info(f"Dispatched alert to {integration.type.value}")
            except Exception as e:
                logger.error(f"Failed to dispatch alert to {integration.type.value}: {e}")

async def get_alerts(db: AsyncSession, location_id: UUID) -> List[CrisisAlert]:
    result = await db.execute(select(CrisisAlert).filter(CrisisAlert.location_id == location_id).order_by(CrisisAlert.created_at.desc()))
    return list(result.scalars().all())

async def resolve_alert(db: AsyncSession, alert_id: UUID) -> Optional[CrisisAlert]:
    result = await db.execute(select(CrisisAlert).filter(CrisisAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert and alert.status == AlertStatus.open:
        alert.status = AlertStatus.resolved
        alert.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)
    return alert

async def get_integrations(db: AsyncSession, location_id: UUID) -> List[AlertIntegration]:
    result = await db.execute(select(AlertIntegration).filter(AlertIntegration.location_id == location_id))
    return list(result.scalars().all())

async def upsert_integration(db: AsyncSession, location_id: UUID, type: IntegrationType, webhook_url: str, is_active: bool) -> AlertIntegration:
    result = await db.execute(select(AlertIntegration).filter(
        AlertIntegration.location_id == location_id,
        AlertIntegration.type == type
    ))
    integration = result.scalar_one_or_none()
    
    if integration:
        integration.webhook_url = webhook_url
        integration.is_active = is_active
    else:
        integration = AlertIntegration(
            location_id=location_id,
            type=type,
            webhook_url=webhook_url,
            is_active=is_active
        )
        db.add(integration)
        
    await db.commit()
    await db.refresh(integration)
    return integration
