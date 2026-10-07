"""add quota columns to users

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('searches_today', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_search_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_search_date')
    op.drop_column('users', 'searches_today')
