"""Add search trigger

Revision ID: 002
Revises: 001
Create Date: 2026-02-22
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION posts_search_vector_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_posts_search_vector
            BEFORE INSERT OR UPDATE OF title, body ON posts
            FOR EACH ROW EXECUTE FUNCTION posts_search_vector_trigger()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_posts_search_vector ON posts;")
    op.execute("DROP FUNCTION IF EXISTS posts_search_vector_trigger();")
