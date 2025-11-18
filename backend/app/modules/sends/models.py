from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Boolean, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from sqlalchemy.sql import func


class UserSubscription(Base):
    """Abonnement (lien entre un utilisateur et un SubscriptionPlan / PricingPlan)
    Correspond à «Abonnement» dans la demande.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subscription_plan_id = Column(Integer, ForeignKey("subscriptionplan.id"), nullable=True)
    pricing_plan_id = Column(Integer, ForeignKey("pricingplan.id"), nullable=True)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="subscriptions")
    subscription_plan = relationship("SubscriptionPlan")
    pricing_plan = relationship("PricingPlan")


class Send(Base):
    """Envoi (regroupe un envoi de bulletins) — correspond à «Envoi» demandé.
    Stocke le nombre de bulletins, le prix unitaire utilisé et le montant total calculé.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)
    user_subscription_id = Column(Integer, ForeignKey("usersubscription.id"), nullable=True)
    pricing_plan_id = Column(Integer, ForeignKey("pricingplan.id"), nullable=True)

    nb_bulletins = Column(Integer, nullable=False)
    price_per_bulletin = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)

    invoice_path = Column(String, nullable=True)  # chemin local vers la facture PDF si générée
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="created", nullable=False)  # created, invoiced, paid, failed

    user = relationship("User")
    tenant = relationship("Tenant")
    user_subscription = relationship("UserSubscription")
    pricing_plan = relationship("PricingPlan")

    def __repr__(self):
        return f"<Send(id={self.id}, user_id={self.user_id}, nb={self.nb_bulletins}, total={self.total_amount})>"
