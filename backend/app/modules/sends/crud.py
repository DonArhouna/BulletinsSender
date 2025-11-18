from typing import Optional, List
from sqlalchemy.orm import Session
from app.modules.sends import models, schemas
from app.modules.subscriptions import models as subs_models


class CRUDSend:
    def get(self, db: Session, id: int) -> Optional[models.Send]:
        return db.query(models.Send).filter(models.Send.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, tenant_id: Optional[int] = None, user_id: Optional[int] = None) -> List[models.Send]:
        q = db.query(models.Send)
        if tenant_id is not None:
            q = q.filter(models.Send.tenant_id == tenant_id)
        if user_id is not None:
            q = q.filter(models.Send.user_id == user_id)
        return q.order_by(models.Send.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: schemas.SendCreate, user_id: int, tenant_id: Optional[int] = None) -> models.Send:
        """Create a Send and compute total based on pricing rules.

        Priority to determine price_per_bulletin:
        1. pricing_plan_id provided in request
        2. pricing_plan on UserSubscription (if user_subscription_id provided)
        3. pricing_plan referenced by SubscriptionPlan (SubscriptionPlan.pricing_plan_id)
        4. first active PricingPlan that references the SubscriptionPlan
        """
        # Resolve pricing plan and user_subscription taking into account the
        # active UserSubscription for the given user when not explicitly provided.
        from app.modules.subscriptions import models as subs_models

        pricing = None
        user_subscription = None

        # 1) explicit pricing_plan_id in request
        if getattr(obj_in, 'pricing_plan_id', None):
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == obj_in.pricing_plan_id).first()

        # 2) explicit user_subscription_id in request
        if getattr(obj_in, 'user_subscription_id', None):
            user_subscription = db.query(models.UserSubscription).filter(models.UserSubscription.id == obj_in.user_subscription_id).first()
            if user_subscription and user_subscription.pricing_plan_id:
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_subscription.pricing_plan_id).first()

        # 2b) If no user_subscription provided, try to find an active subscription for this user
        # OR use the user's direct subscription_plan_id and pricing_plan_id from User table
        if not user_subscription:
            # First try UserSubscription table
            try:
                user_subscription = db.query(models.UserSubscription).filter(models.UserSubscription.user_id == user_id, models.UserSubscription.is_active == True).order_by(models.UserSubscription.start_date.desc()).first()
            except Exception:
                user_subscription = None

            # If no UserSubscription, use direct fields from User table
            if not user_subscription:
                from app.modules.users import models as user_models
                user_obj = db.query(user_models.User).filter(user_models.User.id == user_id).first()
                if user_obj and user_obj.pricing_plan_id:
                    pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_obj.pricing_plan_id).first()
                elif user_obj and user_obj.subscription_plan_id:
                    # Try to find a pricing plan for this subscription plan
                    candidates = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.subscription_plan_id == user_obj.subscription_plan_id, subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).all()
                    if candidates:
                        pricing = candidates[0]

            if user_subscription and user_subscription.pricing_plan_id and not pricing:
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_subscription.pricing_plan_id).first()

        # 3) subscription plan default pricing_plan_id (from user_subscription.subscription_plan)
        if not pricing and user_subscription and user_subscription.subscription_plan_id:
            sp = db.query(subs_models.SubscriptionPlan).filter(subs_models.SubscriptionPlan.id == user_subscription.subscription_plan_id).first()
            if sp and getattr(sp, 'pricing_plan_id', None):
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == sp.pricing_plan_id).first()

        # 4) fallback: get any active PricingPlan linked to the subscription plan
        if not pricing and user_subscription and user_subscription.subscription_plan_id:
            candidates = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.subscription_plan_id == user_subscription.subscription_plan_id, subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).all()
            if candidates:
                pricing = candidates[0]

        # 5) final fallback: any global active pricing plan
        if not pricing:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).first()

        if not pricing:
            raise ValueError("Aucun Forfait/PricingPlan actif trouvé pour calculer le montant")

        price = float(pricing.price_per_bulletin)
        total = round(price * float(obj_in.nb_bulletins), 2)

        db_obj = models.Send(
            user_id=user_id,
            tenant_id=tenant_id,
            user_subscription_id=getattr(obj_in, 'user_subscription_id', None) or (user_subscription.id if user_subscription else None),
            pricing_plan_id=pricing.id,
            nb_bulletins=obj_in.nb_bulletins,
            price_per_bulletin=price,
            total_amount=total,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def recompute_totals(self, db: Session, send_obj: models.Send) -> models.Send:
        """Recompute price_per_bulletin and total_amount for an existing Send.

        This will try to reuse the same resolution order as create(): explicit pricing_plan_id,
        then user_subscription (existing or active for the user), subscription plan defaults, then global fallback.
        """
        from app.modules.subscriptions import models as subs_models

        pricing = None
        user_subscription = None

        # If send already has explicit pricing_plan_id, use it
        if getattr(send_obj, 'pricing_plan_id', None):
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == send_obj.pricing_plan_id).first()

        # If send references a user_subscription, load it
        if getattr(send_obj, 'user_subscription_id', None):
            user_subscription = db.query(models.UserSubscription).filter(models.UserSubscription.id == send_obj.user_subscription_id).first()

        # If no user_subscription attached, try to find active by user
        # OR use the user's direct subscription_plan_id and pricing_plan_id from User table
        if not user_subscription:
            # First try UserSubscription table
            try:
                user_subscription = db.query(models.UserSubscription).filter(models.UserSubscription.user_id == send_obj.user_id, models.UserSubscription.is_active == True).order_by(models.UserSubscription.start_date.desc()).first()
            except Exception:
                user_subscription = None

            # If no UserSubscription, use direct fields from User table
            if not user_subscription:
                from app.modules.users import models as user_models
                user_obj = db.query(user_models.User).filter(user_models.User.id == send_obj.user_id).first()
                if user_obj and user_obj.pricing_plan_id and not pricing:
                    pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_obj.pricing_plan_id).first()
                elif user_obj and user_obj.subscription_plan_id:
                    # Try to find a pricing plan for this subscription plan
                    candidates = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.subscription_plan_id == user_obj.subscription_plan_id, subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).all()
                    if candidates:
                        pricing = candidates[0]

        # Resolve pricing similarly to create()
        if not pricing and user_subscription and user_subscription.pricing_plan_id:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_subscription.pricing_plan_id).first()

        if not pricing and user_subscription and user_subscription.subscription_plan_id:
            sp = db.query(subs_models.SubscriptionPlan).filter(subs_models.SubscriptionPlan.id == user_subscription.subscription_plan_id).first()
            if sp and getattr(sp, 'pricing_plan_id', None):
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == sp.pricing_plan_id).first()

        if not pricing and user_subscription and user_subscription.subscription_plan_id:
            candidates = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.subscription_plan_id == user_subscription.subscription_plan_id, subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).all()
            if candidates:
                pricing = candidates[0]

        if not pricing:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).first()

        if not pricing:
            raise ValueError("Aucun Forfait/PricingPlan actif trouvé pour recalculer le montant")

        price = float(pricing.price_per_bulletin)
        total = round(price * float(send_obj.nb_bulletins), 2)

        send_obj.price_per_bulletin = price
        send_obj.total_amount = total
        send_obj.pricing_plan_id = pricing.id
        # Keep user_subscription_id if present; otherwise set if we discovered one
        if not send_obj.user_subscription_id and user_subscription:
            send_obj.user_subscription_id = user_subscription.id

        db.add(send_obj)
        db.commit()
        db.refresh(send_obj)
        return send_obj

    def recalc_total(self, db: Session, send_obj: models.Send) -> models.Send:
        """Recalculate price_per_bulletin and total_amount for an existing Send
        using the same priority logic as create(). Updates and returns the send object.
        """
        from app.modules.subscriptions import models as subs_models

        pricing = None

        # Try pricing from explicit pricing_plan_id on send
        if send_obj.pricing_plan_id:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == send_obj.pricing_plan_id).first()

        # If not, try user's active subscription OR direct user fields
        user_subscription = None
        if not pricing and send_obj.user_id:
            # First try UserSubscription table
            user_subscription = (
                db.query(models.UserSubscription)
                .filter(models.UserSubscription.user_id == send_obj.user_id, models.UserSubscription.is_active == True)
                .order_by(models.UserSubscription.created_at.desc())
                .first()
            )
            if user_subscription and user_subscription.pricing_plan_id:
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_subscription.pricing_plan_id).first()

            # If no UserSubscription, use direct fields from User table
            if not pricing:
                from app.modules.users import models as user_models
                user_obj = db.query(user_models.User).filter(user_models.User.id == send_obj.user_id).first()
                if user_obj and user_obj.pricing_plan_id:
                    pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == user_obj.pricing_plan_id).first()
                elif user_obj and user_obj.subscription_plan_id:
                    # Try to find a pricing plan for this subscription plan
                    candidates = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.subscription_plan_id == user_obj.subscription_plan_id, subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).all()
                    if candidates:
                        pricing = candidates[0]

        # subscription plan default
        if not pricing and user_subscription and user_subscription.subscription_plan_id:
            sp = db.query(subs_models.SubscriptionPlan).filter(subs_models.SubscriptionPlan.id == user_subscription.subscription_plan_id).first()
            if sp and getattr(sp, 'pricing_plan_id', None):
                pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id == sp.pricing_plan_id).first()

        # fallback: any active pricing
        if not pricing:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.is_active == True).order_by(subs_models.PricingPlan.id.desc()).first()

        if not pricing:
            raise ValueError("Aucun Forfait/PricingPlan actif trouvé pour recalculer le montant")

        price = float(pricing.price_per_bulletin)
        total = round(price * float(send_obj.nb_bulletins), 2)

        send_obj.price_per_bulletin = price
        send_obj.total_amount = total
        send_obj.pricing_plan_id = pricing.id
        db.add(send_obj)
        db.commit()
        db.refresh(send_obj)
        return send_obj


class CRUDUserSubscription:
    def get(self, db: Session, id: int) -> Optional[models.UserSubscription]:
        return db.query(models.UserSubscription).filter(models.UserSubscription.id == id).first()

    def create(self, db: Session, *, obj_in: schemas.UserSubscriptionCreate) -> models.UserSubscription:
        db_obj = models.UserSubscription(
            user_id=obj_in.user_id,
            subscription_plan_id=obj_in.subscription_plan_id,
            pricing_plan_id=obj_in.pricing_plan_id,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


send = CRUDSend()
user_subscription = CRUDUserSubscription()
