import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from httpx import AsyncClient, Timeout
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.schemas.webhooks import EVENT_TYPES

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]

def _sign_payload(payload: Dict[str, Any], secret: str) -> str:
    body = json.dumps(payload, separators=(",", ":"))
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

async def dispatch_event(
    agency_id: UUID,
    event_type: str,
    payload: Dict[str, Any],
) -> None:
    if event_type not in EVENT_TYPES and not event_type.startswith("webhook."):
        logger.warning("Unknown event type: %s", event_type)
        return
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WebhookEndpoint).filter(
                    WebhookEndpoint.agency_id == agency_id,
                    WebhookEndpoint.is_active == True,
                )
            )
            endpoints = result.scalars().all()
        for endpoint in endpoints:
            if event_type in endpoint.event_types or "*" in endpoint.event_types:
                await _send_webhook(endpoint, event_type, payload)
    except Exception as e:
        logger.error("Webhook dispatch error: %s", e)

async def _send_webhook(
    endpoint: WebhookEndpoint,
    event_type: str,
    payload: Dict[str, Any],
    attempt: int = 1,
) -> None:
    body = {
        "event": event_type,
        "id": str(endpoint.id),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    headers = {"Content-Type": "application/json"}
    if endpoint.secret:
        headers["X-Webhook-Signature"] = _sign_payload(body, endpoint.secret)
    try:
        async with AsyncClient(timeout=Timeout(10.0)) as client:
            resp = await client.post(
                endpoint.url,
                json=body,
                headers=headers,
            )
        success = 200 <= resp.status_code < 300
        async with AsyncSessionLocal() as db:
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_type=event_type,
                payload=payload,
                response_status=resp.status_code,
                response_body=resp.text[:2000],
                success=success,
                attempt=attempt,
                delivered_at=datetime.now(timezone.utc) if success else None,
                next_retry_at=(datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAYS[attempt])) if not success and attempt < MAX_RETRIES else None,
            )
            db.add(delivery)

            ep = await db.execute(select(WebhookEndpoint).filter(WebhookEndpoint.id == endpoint.id))
            ep = ep.scalar_one()
            if success:
                ep.last_success_at = datetime.now(timezone.utc)
                ep.failure_count = 0
            else:
                ep.last_failure_at = datetime.now(timezone.utc)
                ep.failure_count = WebhookEndpoint.failure_count + 1

            await db.commit()

        if not success and attempt < MAX_RETRIES:
            logger.info("Webhook delivery failed (attempt %d/%d), will retry", attempt, MAX_RETRIES)
    except Exception as e:
        logger.error("Webhook send error: %s", e)
        async with AsyncSessionLocal() as db:
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_type=event_type,
                payload=payload,
                success=False,
                attempt=attempt,
                next_retry_at=(datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAYS[attempt])) if attempt < MAX_RETRIES else None,
            )
            db.add(delivery)
            await db.commit()

async def retry_failed_deliveries() -> None:
    logger.info("Checking for failed webhook deliveries to retry...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WebhookDelivery).filter(
                WebhookDelivery.success == False,
                WebhookDelivery.next_retry_at <= datetime.now(timezone.utc),
                WebhookDelivery.attempt < MAX_RETRIES,
            )
        )
        deliveries = result.scalars().all()
        for delivery in deliveries:
            ep_result = await db.execute(select(WebhookEndpoint).filter(WebhookEndpoint.id == delivery.endpoint_id))
            ep = ep_result.scalar_one_or_none()
            if not ep or not ep.is_active:
                continue
            await _send_webhook(ep, delivery.event_type, delivery.payload, delivery.attempt + 1)

async def list_endpoints(db: AsyncSession, agency_id: UUID) -> List[WebhookEndpoint]:
    result = await db.execute(
        select(WebhookEndpoint).filter(WebhookEndpoint.agency_id == agency_id).order_by(WebhookEndpoint.created_at.desc())
    )
    return result.scalars().all()

async def create_endpoint(db: AsyncSession, agency_id: UUID, data: dict) -> WebhookEndpoint:
    ep = WebhookEndpoint(agency_id=agency_id, **data)
    db.add(ep)
    await db.commit()
    await db.refresh(ep)
    return ep

async def update_endpoint(db: AsyncSession, agency_id: UUID, endpoint_id: UUID, data: dict) -> WebhookEndpoint:
    result = await db.execute(
        select(WebhookEndpoint).filter(WebhookEndpoint.id == endpoint_id, WebhookEndpoint.agency_id == agency_id)
    )
    ep = result.scalar_one_or_none()
    if not ep:
        raise ValueError("Endpoint not found")
    for k, v in data.items():
        if v is not None:
            setattr(ep, k, v)
    await db.commit()
    await db.refresh(ep)
    return ep

async def delete_endpoint(db: AsyncSession, agency_id: UUID, endpoint_id: UUID) -> None:
    result = await db.execute(
        select(WebhookEndpoint).filter(WebhookEndpoint.id == endpoint_id, WebhookEndpoint.agency_id == agency_id)
    )
    ep = result.scalar_one_or_none()
    if not ep:
        raise ValueError("Endpoint not found")
    await db.delete(ep)
    await db.commit()

async def list_deliveries(db: AsyncSession, agency_id: UUID, endpoint_id: Optional[UUID] = None, limit: int = 50) -> List[WebhookDelivery]:
    query = select(WebhookDelivery).join(WebhookEndpoint).filter(WebhookEndpoint.agency_id == agency_id)
    if endpoint_id:
        query = query.filter(WebhookDelivery.endpoint_id == endpoint_id)
    query = query.order_by(WebhookDelivery.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
