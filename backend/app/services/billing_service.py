import razorpay
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Agency
from app.config import get_settings

settings = get_settings()

class BillingService:
    def __init__(self):
        # We can configure Razorpay client if keys are present
        # For local dev without keys, we mock the responses
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None

    async def create_checkout_session(self, agency: Agency, plan_id: str) -> Dict[str, Any]:
        """
        Creates a Razorpay order for the selected plan.
        Returns the order details for the frontend to initialize Razorpay Checkout.
        """
        # Determine amount based on plan
        amount = 0
        if plan_id == "pro":
            amount = 4900 # $49.00 in cents (or INR equivalent)
        elif plan_id == "starter":
            amount = 1900
            
        if not self.client:
            # Return mock order
            return {
                "id": f"order_mock_{agency.id}_{plan_id}",
                "amount": amount,
                "currency": "USD",
                "status": "created"
            }

        # Real Razorpay integration
        order_data = {
            "amount": amount,
            "currency": "USD",
            "receipt": f"receipt_{agency.id}",
            "notes": {
                "agency_id": str(agency.id),
                "plan": plan_id
            }
        }
        order = self.client.order.create(data=order_data)
        return order

    async def handle_webhook(self, db: AsyncSession, payload: Dict[str, Any]) -> None:
        """
        Process Razorpay webhooks (e.g., payment captured, subscription active)
        """
        # This would typically verify the webhook signature and update DB
        event_type = payload.get("event")
        if event_type == "payment.captured":
            # Find the agency and upgrade them
            pass
        
    def start_trial(self) -> datetime:
        """Return the trial end date (14 days from now)"""
        return datetime.utcnow() + timedelta(days=14)

billing_service = BillingService()
