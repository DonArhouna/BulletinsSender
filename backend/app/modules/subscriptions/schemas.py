from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class SubscriptionPlanBase(BaseModel):
    name: str
    duration_months: int
    is_active: Optional[bool] = True


class SubscriptionPlanCreate(SubscriptionPlanBase):
    # Allow selecting a pricing_plan (Forfait) when creating a Subscription (Abonnement)
    pricing_plan_id: Optional[int] = None


class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    duration_months: Optional[int] = None
    is_active: Optional[bool] = None
    pricing_plan_id: Optional[int] = None


class SubscriptionPlan(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PricingPlanBase(BaseModel):
    # A PricingPlan (Forfait) may be independent — keep subscription_plan_id optional for compatibility
    subscription_plan_id: Optional[int] = None
    price_per_bulletin: float
    currency: Optional[str] = "EUR"
    is_active: Optional[bool] = True


class PricingPlanCreate(PricingPlanBase):
    pass


class PricingPlanUpdate(BaseModel):
    subscription_plan_id: Optional[int] = None
    price_per_bulletin: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class PricingPlan(PricingPlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True