"""Add activation KPI columns to agencies (time-to-first-sync, time-to-first-AI-reply)

Revision ID: 004_add_activation_kpis
Revises: 003_widen_oauth_secret
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_add_activation_kpis"
down_revision: Union[str, None] = "003_widen_oauth_secret"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("first_synced_at", sa.DateTime(), nullable=True))
    op.add_column("agencies", sa.Column("first_ai_reply_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("agencies", "first_ai_reply_at")
    op.drop_column("agencies", "first_synced_at")
