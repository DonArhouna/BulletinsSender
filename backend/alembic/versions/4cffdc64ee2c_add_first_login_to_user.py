"""add_first_login_to_user

Revision ID: 4cffdc64ee2c
Revises: 00b2be4693ed
Create Date: 2025-10-20 16:10:10.492962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cffdc64ee2c'
down_revision: Union[str, Sequence[str], None] = '00b2be4693ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ajouter la colonne first_login à la table user
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('user')] if inspector.has_table('user') else []
    if 'first_login' not in cols:
        op.add_column('user', sa.Column('first_login', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer la colonne first_login de la table user
    op.drop_column('user', 'first_login')
