"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="STUDENT"),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tags",
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text),
    )

    op.create_table(
        "posts",
        sa.Column("post_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("vote_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("answer_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_pinned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("search_vector", postgresql.TSVECTOR),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_posts_created_at", "posts", ["created_at"])
    op.create_index("idx_posts_status", "posts", ["status"])
    op.create_index("idx_posts_author_id", "posts", ["author_id"])
    op.create_index("idx_posts_search", "posts", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "post_tags",
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.post_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "answers",
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_accepted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("vote_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_answers_post_id", "answers", ["post_id"])
    op.create_index("idx_answers_author_id", "answers", ["author_id"])

    op.create_table(
        "comments",
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.post_id", ondelete="CASCADE")),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answers.answer_id", ondelete="CASCADE")),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_comments_post_id", "comments", ["post_id"])
    op.create_index("idx_comments_answer_id", "comments", ["answer_id"])

    op.create_table(
        "votes",
        sa.Column("vote_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.post_id", ondelete="CASCADE")),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answers.answer_id", ondelete="CASCADE")),
        sa.Column("vote_type", sa.String(4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", name="uq_vote_post_user"),
        sa.UniqueConstraint("answer_id", "user_id", name="uq_vote_answer_user"),
        sa.CheckConstraint(
            "(post_id IS NOT NULL AND answer_id IS NULL) OR (post_id IS NULL AND answer_id IS NOT NULL)",
            name="chk_vote_target",
        ),
    )
    op.create_index("idx_votes_user_id", "votes", ["user_id"])

    op.create_table(
        "notifications",
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_is_read", "notifications", ["is_read"])

    op.create_table(
        "attachments",
        sa.Column("attachment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.post_id", ondelete="CASCADE")),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_attachments_post_id", "attachments", ["post_id"])


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("notifications")
    op.drop_table("votes")
    op.drop_table("comments")
    op.drop_table("answers")
    op.drop_table("post_tags")
    op.drop_table("posts")
    op.drop_table("tags")
    op.drop_table("users")
