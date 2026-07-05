"""Add sentiment_results.model so keyword-fallback output is distinguishable from LLM output

Revision ID: 005_add_sentiment_model
Revises: 004_add_activation_kpis
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_add_sentiment_model"
down_revision: Union[str, None] = "004_add_activation_kpis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sentiment_results", sa.Column("model", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("sentiment_results", "model")
