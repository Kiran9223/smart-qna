"""add cognito_sub drop password and role

Revision ID: 003
Revises: 002
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add cognito_sub as nullable first to handle existing rows
    op.add_column('users', sa.Column('cognito_sub', sa.String(255), nullable=True))
    # Fill existing rows with a placeholder so NOT NULL can be applied
    op.execute("UPDATE users SET cognito_sub = gen_random_uuid()::text WHERE cognito_sub IS NULL")
    op.alter_column('users', 'cognito_sub', nullable=False)
    op.create_unique_constraint('uq_users_cognito_sub', 'users', ['cognito_sub'])
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'role')


def downgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=True))
    op.drop_constraint('uq_users_cognito_sub', 'users', type_='unique')
    op.drop_column('users', 'cognito_sub')
