"""add store preference columns

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-10-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a1b2'
down_revision = 'b2c3d4e5f6a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users_preferences', sa.Column('search_emag', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users_preferences', sa.Column('search_altex', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('users_preferences', 'search_altex')
    op.drop_column('users_preferences', 'search_emag')
