from app.db import base
from app.db.session import SessionLocal
from app.modules.sends import models as s_mod
from app.modules.subscriptions import models as sub_mod
from app.modules.users import models as u_mod


db=SessionLocal()
try:
    subs = db.query(s_mod.UserSubscription).all()
    print('UserSubscriptions:', len(subs))
    for us in subs:
        print('US id', us.id, 'user_id', us.user_id, 'sub_plan', us.subscription_plan_id, 'pricing', us.pricing_plan_id, 'active', us.is_active)
    sps = db.query(sub_mod.SubscriptionPlan).all()
    print('SubscriptionPlans:', len(sps))
    for sp in sps:
        print('SP', sp.id, getattr(sp,'name',None), 'pricing_plan_id', getattr(sp,'pricing_plan_id',None))
    pps = db.query(sub_mod.PricingPlan).all()
    print('PricingPlans:', len(pps))
    for pp in pps:
        print('PP', pp.id, 'price_per_bulletin', getattr(pp,'price_per_bulletin',None), 'subscription_plan_id', getattr(pp,'subscription_plan_id',None), 'is_active', getattr(pp,'is_active',None))
    users = db.query(u_mod.User).all()
    print('Users:', len(users))
    for u in users:
        print('User', u.id, u.email, 'tenant', u.tenant_id)
finally:
    db.close()
