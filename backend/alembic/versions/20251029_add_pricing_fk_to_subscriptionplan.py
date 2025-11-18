"""Add pricing_plan_id to subscriptionplan and backfill

Revision ID: 20251029_add_pricing_fk_to_subscriptionplan
Revises: 9b1f2c7a1ab3
Create Date: 2025-10-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
# Use a shorter revision id so it fits alembic_version column
revision = '20251029_addprf'
# This migration was replaced by a shorter-id migration; make this a no-op and depend on the new short-id migration
down_revision = '20251029_pricingfk'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: replaced by 20251029_pricingfk
    pass


def downgrade() -> None:
    # No-op
    pass
