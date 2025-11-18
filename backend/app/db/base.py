from app.db.base_class import Base

# Import all models here so that Base has them before being imported by Alembic
# Use module-based models to avoid duplicate table definitions
from app.modules.users.models import Tenant, User
from app.modules.emails.models import Email
from app.modules.subscriptions.models import SubscriptionPlan, PricingPlan
from app.modules.sends.models import Send, UserSubscription
