from app.db.session import SessionLocal
from app.modules.subscriptions import crud as subs_crud
from app.modules.users import crud as users_crud


def run():
    db = SessionLocal()
    try:
        # create pricing plan
        pricing_in = type('P', (), {'subscription_plan_id': None, 'price_per_bulletin': 1.23, 'currency':'EUR','is_active':True})
        p = subs_crud.pricing_plan.create(db, obj_in=pricing_in)
        print('Created pricing plan id=', p.id)
        # create subscription referencing this pricing
        sub_in = type('S', (), {'name':'TESTSUB','duration_months':1,'is_active':True,'pricing_plan_id':p.id})
        s = subs_crud.subscription_plan.create(db, obj_in=sub_in)
        print('Created subscription id=', s.id, 'pricing_plan_id=', s.pricing_plan_id)
        # create user with subscription only
        user_in = type('U', (), {'email':'test@example.com','password':'pass','full_name':'Test','is_active':True,'is_superuser':False,'subscription_plan_id':s.id,'pricing_plan_id':None,'username':None,'company':None,'first_login':True})
        u = users_crud.user.create(db, obj_in=user_in)
        print('Created user id=', u.id, 'subscription=', u.subscription_plan_id, 'pricing=', u.pricing_plan_id)
    finally:
        db.rollback()
        db.close()

if __name__ == '__main__':
    run()
