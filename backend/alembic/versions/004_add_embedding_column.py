"""Add embedding vector column to posts for AI similarity search

Revision ID: 004
Revises: 003
Create Date: 2026-03-10
"""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_posts_embedding
        ON posts
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_posts_embedding")
    op.execute("ALTER TABLE posts DROP COLUMN IF EXISTS embedding")
