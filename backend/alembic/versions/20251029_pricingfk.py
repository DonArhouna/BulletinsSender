"""Add pricing_plan_id to subscriptionplan and backfill

Revision ID: 20251029_pricingfk
Revises: 9b1f2c7a1ab3
Create Date: 2025-10-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251029_pricingfk'
down_revision = '9b1f2c7a1ab3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable pricing_plan_id to subscriptionplan
    op.add_column('subscriptionplan', sa.Column('pricing_plan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('subscriptionplan_pricing_plan_fk', 'subscriptionplan', 'pricingplan', ['pricing_plan_id'], ['id'])

    # Backfill: set subscriptionplan.pricing_plan_id to one of the existing pricingplan ids that referenced the subscription (if any)
    # Use DISTINCT ON to pick the first pricingplan per subscription
    op.execute("""
    UPDATE subscriptionplan
    SET pricing_plan_id = sub.id
    FROM (
        SELECT DISTINCT ON (subscription_plan_id) id, subscription_plan_id
        FROM pricingplan
        WHERE subscription_plan_id IS NOT NULL
        ORDER BY subscription_plan_id, id
    ) AS sub
    WHERE subscriptionplan.id = sub.subscription_plan_id;
    """)


def downgrade() -> None:
    # Drop FK and column
    op.drop_constraint('subscriptionplan_pricing_plan_fk', 'subscriptionplan', type_='foreignkey')
    op.drop_column('subscriptionplan', 'pricing_plan_id')
