from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class SubscriptionPlan(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    duration_months = Column(Integer, nullable=False)  # 1, 6, 12
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # pricing_plans: historical/owned PricingPlan rows that reference this SubscriptionPlan
    # Historical PricingPlan rows that reference this SubscriptionPlan are stored in PricingPlan.subscription_plan_id
    # New: link to a default PricingPlan (Forfait) — a SubscriptionPlan (Abonnement) can reference a PricingPlan
    pricing_plan_id = Column(Integer, ForeignKey("pricingplan.id"), nullable=True)

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, duration={self.duration_months}m)>"


class PricingPlan(Base):
    id = Column(Integer, primary_key=True, index=True)
    # keep the existing column for backward compatibility; the new preferred relation
    # is that SubscriptionPlan points to a PricingPlan (pricing_plan_id on SubscriptionPlan).
    subscription_plan_id = Column(Integer, ForeignKey("subscriptionplan.id"), nullable=True)
    price_per_bulletin = Column(Float, nullable=False)
    currency = Column(String, default="EUR", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # PricingPlan may reference a SubscriptionPlan via subscription_plan_id (historical linkage)
    subscription_plan_id = Column(Integer, ForeignKey("subscriptionplan.id"), nullable=True)

    def __repr__(self):
        return f"<PricingPlan(subscription_plan_id={self.subscription_plan_id}, price={self.price_per_bulletin} {self.currency})>"