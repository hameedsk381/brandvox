"""Widen agencies.google_oauth_client_secret for encrypted-at-rest values

Revision ID: 003_widen_oauth_secret
Revises: 2d016c736084
Create Date: 2026-07-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_widen_oauth_secret"
down_revision: Union[str, None] = "2d016c736084"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "agencies",
        "google_oauth_client_secret",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "agencies",
        "google_oauth_client_secret",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
