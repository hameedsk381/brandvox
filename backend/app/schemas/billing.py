from pydantic import BaseModel
from typing import Optional
from datetime import datetime

PLANS = {
    "trial": {"name": "Free Trial", "amount": 0, "features": ["1 location", "Basic AI replies", "Standard reporting"]},
    "starter": {"name": "Starter", "amount": 1900, "features": ["Up to 3 locations", "Standard AI replies", "Basic reporting", "Email support"]},
    "pro": {"name": "Pro", "amount": 4900, "features": ["Unlimited locations", "Advanced AI Copilot", "Competitor & Forecasting", "Custom branding", "Priority support", "API access", "Webhook integrations"]},
    "enterprise": {"name": "Enterprise", "amount": 0, "features": ["Everything in Pro", "SSO/SAML", "Dedicated support", "Custom SLA", "On-premise option"]},
}

class CheckoutRequest(BaseModel):
    plan_id: str

class BillingStatusResponse(BaseModel):
    subscription_plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    is_trial_active: bool = False

class PlanInfo(BaseModel):
    id: str
    name: str
    amount: int
    features: list[str]

class BillingUpdateRequest(BaseModel):
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
