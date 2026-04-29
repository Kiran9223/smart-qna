"""Add notification event/idempotency fields

Revision ID: 005
Revises: 004
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("source_event_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "delivery_source",
            sa.String(length=20),
            nullable=False,
            server_default="direct",
        ),
    )
    op.create_index(
        "uq_notifications_source_event_id",
        "notifications",
        ["source_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_notifications_source_event_id", table_name="notifications")
    op.drop_column("notifications", "delivery_source")
    op.drop_column("notifications", "source_event_id")
