from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.modules.emails.models import Email
from app.modules.subscriptions.models import SubscriptionPlan, PricingPlan


class User(Base):
    """
    User model with multi-tenant support
    """
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    first_login = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)
    # Link to subscription (Abonnement) and pricing (Forfait)
    subscription_plan_id = Column(Integer, ForeignKey("subscriptionplan.id"), nullable=True)
    pricing_plan_id = Column(Integer, ForeignKey("pricingplan.id"), nullable=True)
    subscription_plan_id = Column(Integer, ForeignKey("subscriptionplan.id"), nullable=True)
    pricing_plan_id = Column(Integer, ForeignKey("pricingplan.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    subscription_plan = relationship("SubscriptionPlan")
    pricing_plan = relationship("PricingPlan")
    subscription_plan = relationship("SubscriptionPlan")
    pricing_plan = relationship("PricingPlan")

    def __repr__(self):
        return f"<User(email={self.email}, tenant_id={self.tenant_id})>"


class Tenant(Base):
    """
    Multi-tenant model for isolating client data
    """
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant")
    emails = relationship("Email", back_populates="tenant")
