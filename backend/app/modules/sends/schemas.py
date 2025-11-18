from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserSubscriptionBase(BaseModel):
    user_id: int
    subscription_plan_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None
    is_active: Optional[bool] = True


class UserSubscriptionCreate(UserSubscriptionBase):
    pass


class UserSubscription(UserSubscriptionBase):
    id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SendCreate(BaseModel):
    nb_bulletins: int
    user_subscription_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None


class Send(BaseModel):
    id: int
    user_id: int
    tenant_id: Optional[int] = None
    user_subscription_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None
    nb_bulletins: int
    price_per_bulletin: float
    total_amount: float
    invoice_path: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    status: Optional[str] = None
    created_at: datetime
    pricing_plan: Optional[dict] = None  # Add pricing_plan relation

    class Config:
        from_attributes = True
