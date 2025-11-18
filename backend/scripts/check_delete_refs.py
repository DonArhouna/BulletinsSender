import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import project settings
from app.core.config import settings
from app.db.base import Base
from app.modules.subscriptions import models as sub_models
from app.modules.users import models as user_models


def main(args):
    db_url = settings.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    pricing_id = int(args[0]) if len(args) > 0 else None
    sub_id = int(args[1]) if len(args) > 1 else None

    if pricing_id is not None:
        users_count = session.query(user_models.User).filter(user_models.User.pricing_plan_id == pricing_id).count()
        subs_default_count = session.query(sub_models.SubscriptionPlan).filter(sub_models.SubscriptionPlan.pricing_plan_id == pricing_id).count()
        print(f"Pricing id={pricing_id}: users referencing: {users_count}, subscription defaults referencing: {subs_default_count}")

    if sub_id is not None:
        pricing_count = session.query(sub_models.PricingPlan).filter(sub_models.PricingPlan.subscription_plan_id == sub_id).count()
        users_sub_count = session.query(user_models.User).filter(user_models.User.subscription_plan_id == sub_id).count()
        print(f"Subscription id={sub_id}: pricing referencing: {pricing_count}, users referencing: {users_sub_count}")

    session.close()

if __name__ == '__main__':
    main(sys.argv[1:])
