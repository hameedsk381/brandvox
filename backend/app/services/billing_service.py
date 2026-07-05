import razorpay
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tenant import Agency
from app.schemas.billing import PLANS
from app.config import get_settings

settings = get_settings()

class BillingService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID or None
        self.key_secret = settings.RAZORPAY_KEY_SECRET or None
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None

    async def create_checkout_session(self, agency: Agency, plan_id: str) -> Dict[str, Any]:
        plan = PLANS.get(plan_id)
        if not plan or plan["amount"] <= 0:
            return {"id": f"free_{agency.id}_{plan_id}", "amount": 0, "currency": "USD", "status": "created", "plan_id": plan_id}

        amount = plan["amount"]
        if not self.client:
            return {
                "id": f"order_mock_{agency.id}_{plan_id}",
                "amount": amount,
                "currency": "USD",
                "status": "created",
                "plan_id": plan_id,
            }

        order_data = {
            "amount": amount,
            "currency": "USD",
            "receipt": f"receipt_{agency.id}_{plan_id}",
            "notes": {"agency_id": str(agency.id), "plan": plan_id},
        }
        order = self.client.order.create(data=order_data)
        order["plan_id"] = plan_id
        return order

    def verify_webhook_signature(self, raw_body: bytes, signature: Optional[str]) -> bool:
        """Razorpay signs the raw request body with HMAC-SHA256 (hex) using the
        webhook secret. This webhook grants subscriptions, so unsigned or
        unverifiable requests must be rejected — never processed on trust."""
        current = get_settings()
        secret = current.RAZORPAY_WEBHOOK_SECRET or current.RAZORPAY_KEY_SECRET
        if not secret or not signature:
            return False
        expected_sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    async def handle_webhook(self, db: AsyncSession, payload: Dict[str, Any]) -> None:
        event = payload.get("event", "")
        if event == "payment.captured":
            # Only the real Razorpay event shape; no top-level fallbacks.
            notes = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {}) or {}
            agency_id = notes.get("agency_id")
            plan_id = notes.get("plan", "starter")
            if agency_id:
                result = await db.execute(select(Agency).filter(Agency.id == agency_id))
                agency = result.scalar_one_or_none()
                if agency:
                    agency.subscription_plan = plan_id
                    agency.subscription_status = "active"
                    agency.trial_ends_at = None
                    await db.commit()

    def start_trial(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=14)

billing_service = BillingService()
