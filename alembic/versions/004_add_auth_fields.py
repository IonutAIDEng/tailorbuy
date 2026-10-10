"""add auth fields to users and create refresh_tokens

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a1b2
Create Date: 2026-10-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop orphaned table created outside Alembic so we own it going forward
    op.drop_table('refresh_tokens')

    # --- users table ---
    op.drop_column('users', 'device_id')

    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False,
                                     server_default='true'))

    # Set placeholder values for any existing dev rows before enforcing NOT NULL + UNIQUE
    op.execute("UPDATE users SET email = 'legacy_' || id || '@placeholder.dev', "
               "hashed_password = 'placeholder' WHERE email IS NULL")

    op.alter_column('users', 'email', nullable=False)
    op.alter_column('users', 'hashed_password', nullable=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # --- refresh_tokens table (owned by Alembic from this point) ---
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'email')
    op.add_column('users', sa.Column('device_id', sa.String(), nullable=True))
