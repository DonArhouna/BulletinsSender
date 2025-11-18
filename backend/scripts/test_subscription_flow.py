from app.db.session import SessionLocal
from app.modules.subscriptions import crud as subs_crud, schemas as subs_schemas
from app.modules.users import crud as users_crud, schemas as user_schemas


def run():
    db = SessionLocal()
    try:
        print('--- Starting test subscription flow ---')
        # Create a SubscriptionPlan (Abonnement) first
        sub_in = subs_schemas.SubscriptionPlanCreate(name="TestSub", duration_months=1, is_active=True)
        sub = subs_crud.subscription_plan.create(db, obj_in=sub_in)
        print('Created SubscriptionPlan id=', sub.id, 'pricing_plan_id=', getattr(sub, 'pricing_plan_id', None))

        # Create a PricingPlan (Forfait) that references this SubscriptionPlan (DB requires subscription_plan_id non-null)
        pricing_in = subs_schemas.PricingPlanCreate(subscription_plan_id=sub.id, price_per_bulletin=9.99, currency="EUR", is_active=True)
        pricing = subs_crud.pricing_plan.create(db, obj_in=pricing_in)
        print('Created PricingPlan id=', pricing.id)

        # Link the subscription's default pricing_plan_id to the created PricingPlan
        sub = subs_crud.subscription_plan.update(db, db_obj=sub, obj_in={"pricing_plan_id": pricing.id})
        print('Updated SubscriptionPlan id=', sub.id, 'pricing_plan_id=', getattr(sub, 'pricing_plan_id', None))

        # Create a User providing only subscription_plan_id
        user_in = user_schemas.UserCreate(email="testuser+flow@example.com", password="TestPass123!", full_name="Test User", subscription_plan_id=sub.id)
        user = users_crud.user.create(db, obj_in=user_in)
        print('Created User id=', user.id, 'subscription_plan_id=', user.subscription_plan_id, 'pricing_plan_id=', user.pricing_plan_id)

        # Create another subscription+pricing pair for update test
        sub2 = subs_crud.subscription_plan.create(db, obj_in=subs_schemas.SubscriptionPlanCreate(name="TestSub2", duration_months=12, is_active=True))
        pricing2 = subs_crud.pricing_plan.create(db, obj_in=subs_schemas.PricingPlanCreate(subscription_plan_id=sub2.id, price_per_bulletin=19.99, currency="EUR", is_active=True))
        sub2 = subs_crud.subscription_plan.update(db, db_obj=sub2, obj_in={"pricing_plan_id": pricing2.id})
        print('Created sub2:', sub2.id, 'pricing_plan_id:', getattr(sub2, 'pricing_plan_id', None))

        # Update user's subscription
        users_crud.user.update(db, db_obj=user, obj_in={"subscription_plan_id": sub2.id})
        db.refresh(user)
        print('After update User id=', user.id, 'subscription_plan_id=', user.subscription_plan_id, 'pricing_plan_id=', user.pricing_plan_id)

        print('--- Test completed ---')
    finally:
        db.close()


if __name__ == '__main__':
    run()
