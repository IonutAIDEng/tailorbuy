"""add extended preference columns

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users_preferences', sa.Column('min_review_count', sa.Integer(), nullable=True))
    op.add_column('users_preferences', sa.Column('new_only', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users_preferences', 'new_only')
    op.drop_column('users_preferences', 'min_review_count')
