"""Add subscriptions, pricing tables and user FK

Revision ID: 9b1f2c7a1ab3
Revises: 4cffdc64ee2c
Create Date: 2025-10-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b1f2c7a1ab3'
down_revision: Union[str, Sequence[str], None] = '4cffdc64ee2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create subscriptionplan table if missing
    if not inspector.has_table('subscriptionplan'):
        op.create_table(
            'subscriptionplan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('duration_months', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )
    existing = [idx['name'] for idx in inspector.get_indexes('subscriptionplan')] if inspector.has_table('subscriptionplan') else []
    if 'ix_subscriptionplan_id' not in existing:
        op.create_index(op.f('ix_subscriptionplan_id'), 'subscriptionplan', ['id'], unique=False)

    # Create pricingplan table if missing
    if not inspector.has_table('pricingplan'):
        op.create_table(
            'pricingplan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('subscription_plan_id', sa.Integer(), nullable=False),
            sa.Column('price_per_bulletin', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(), nullable=False, server_default='EUR'),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['subscription_plan_id'], ['subscriptionplan.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    existing = [idx['name'] for idx in inspector.get_indexes('pricingplan')] if inspector.has_table('pricingplan') else []
    if 'ix_pricingplan_id' not in existing:
        op.create_index(op.f('ix_pricingplan_id'), 'pricingplan', ['id'], unique=False)

    # Add FK columns to user if missing
    user_cols = [c['name'] for c in inspector.get_columns('user')] if inspector.has_table('user') else []
    if 'subscription_plan_id' not in user_cols:
        op.add_column('user', sa.Column('subscription_plan_id', sa.Integer(), nullable=True))
    if 'pricing_plan_id' not in user_cols:
        op.add_column('user', sa.Column('pricing_plan_id', sa.Integer(), nullable=True))
    # Create foreign keys only if target tables/columns exist
    if inspector.has_table('subscriptionplan') and inspector.has_table('user'):
        fk_names = [fk['name'] for fk in inspector.get_foreign_keys('user')]
        if 'user_subscription_plan_fk' not in fk_names:
            op.create_foreign_key('user_subscription_plan_fk', 'user', 'subscriptionplan', ['subscription_plan_id'], ['id'])
    if inspector.has_table('pricingplan') and inspector.has_table('user'):
        fk_names = [fk['name'] for fk in inspector.get_foreign_keys('user')]
        if 'user_pricing_plan_fk' not in fk_names:
            op.create_foreign_key('user_pricing_plan_fk', 'user', 'pricingplan', ['pricing_plan_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop FKs and columns from user
    op.drop_constraint('user_pricing_plan_fk', 'user', type_='foreignkey')
    op.drop_constraint('user_subscription_plan_fk', 'user', type_='foreignkey')
    op.drop_column('user', 'pricing_plan_id')
    op.drop_column('user', 'subscription_plan_id')

    # Drop pricingplan and subscriptionplan tables
    op.drop_index(op.f('ix_pricingplan_id'), table_name='pricingplan')
    op.drop_table('pricingplan')
    op.drop_index(op.f('ix_subscriptionplan_id'), table_name='subscriptionplan')
    op.drop_table('subscriptionplan')