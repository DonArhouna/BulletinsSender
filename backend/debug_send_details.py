from app.db import base
from app.db.session import SessionLocal
from app.modules.sends import models as sends_models
from app.modules.users import models as user_models
from app.modules.subscriptions import models as subs_models


db = SessionLocal()
try:
    sends = db.query(sends_models.Send).order_by(sends_models.Send.created_at.desc()).limit(20).all()
    for s in sends:
        user = db.query(user_models.User).filter(user_models.User.id==s.user_id).first()
        us = None
        if s.user_subscription_id:
            us = db.query(sends_models.UserSubscription).filter(sends_models.UserSubscription.id==s.user_subscription_id).first()
        pricing = None
        if s.pricing_plan_id:
            pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id==s.pricing_plan_id).first()
        pricing_sub_name = None
        if pricing and getattr(pricing, 'subscription_plan_id', None):
            sp = db.query(subs_models.SubscriptionPlan).filter(subs_models.SubscriptionPlan.id==pricing.subscription_plan_id).first()
            pricing_sub_name = sp.name if sp else None
        print('Send', s.id, 'user', user.email if user else s.user_id, 'nb', s.nb_bulletins, 'price', s.price_per_bulletin, 'total', s.total_amount, 'pricing_id', s.pricing_plan_id, 'pricing_sub', pricing_sub_name, 'user_sub', (us.id if us else None))
finally:
    db.close()
