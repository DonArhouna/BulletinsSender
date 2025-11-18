from app.db import base
from app.db.session import SessionLocal
from app.modules.sends import models as sends_models
from app.modules.users import models as user_models
from app.modules.subscriptions import models as subs_models


def main():
    db = SessionLocal()
    try:
        users = db.query(user_models.User).all()
        print('Users:', len(users))
        for u in users:
            print('USER', u.id, u.email, 'subscription_plan_id:', u.subscription_plan_id, 'pricing_plan_id:', u.pricing_plan_id)
            usubs = db.query(sends_models.UserSubscription).filter(sends_models.UserSubscription.user_id == u.id).order_by(sends_models.UserSubscription.start_date.desc()).all()
            if not usubs:
                print('  No UserSubscription')
            for us in usubs:
                sp = None
                if us.subscription_plan_id:
                    sp = db.query(subs_models.SubscriptionPlan).filter(subs_models.SubscriptionPlan.id==us.subscription_plan_id).first()
                pricing = None
                if us.pricing_plan_id:
                    pricing = db.query(subs_models.PricingPlan).filter(subs_models.PricingPlan.id==us.pricing_plan_id).first()
                print('  US', us.id, 'active', us.is_active, 'start', us.start_date, 'sub_plan', (sp.name if sp else None), 'pricing', (pricing.price_per_bulletin if pricing else None), 'pricing_id', (pricing.id if pricing else None))
    finally:
        db.close()

if __name__ == '__main__':
    main()
