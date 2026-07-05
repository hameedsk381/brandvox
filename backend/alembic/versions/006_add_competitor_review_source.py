"""Add competitor_reviews.source so seeded sample data is distinguishable from real data

Revision ID: 006_add_competitor_source
Revises: 005_add_sentiment_model
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_add_competitor_source"
down_revision: Union[str, None] = "005_add_sentiment_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("competitor_reviews", sa.Column("source", sa.String(length=50), nullable=True))
    # All pre-existing competitor reviews were seeded from templates.
    op.execute("UPDATE competitor_reviews SET source = 'sample' WHERE source IS NULL")


def downgrade() -> None:
    op.drop_column("competitor_reviews", "source")
