"""add google integration observability fields

Revision ID: 002
Revises: 001
Create Date: 2026-07-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("google_integrations", sa.Column("last_sync_status", sa.String(length=50), nullable=True))
    op.add_column("google_integrations", sa.Column("last_sync_error", sa.String(), nullable=True))
    op.add_column("google_integrations", sa.Column("last_sync_attempt_at", sa.DateTime(), nullable=True))
    op.add_column("google_integrations", sa.Column("last_reply_status", sa.String(length=50), nullable=True))
    op.add_column("google_integrations", sa.Column("last_reply_error", sa.String(), nullable=True))
    op.add_column("google_integrations", sa.Column("last_reply_attempt_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("google_integrations", "last_reply_attempt_at")
    op.drop_column("google_integrations", "last_reply_error")
    op.drop_column("google_integrations", "last_reply_status")
    op.drop_column("google_integrations", "last_sync_attempt_at")
    op.drop_column("google_integrations", "last_sync_error")
    op.drop_column("google_integrations", "last_sync_status")
