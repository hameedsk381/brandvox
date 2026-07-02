"""add billing fields

Revision ID: 059c4f5e2eb4
Revises: 002
Create Date: 2026-07-02 16:27:09.757529
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '059c4f5e2eb4'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("razorpay_customer_id", sa.String(255), nullable=True))
    op.add_column("agencies", sa.Column("subscription_plan", sa.String(50), server_default="trial", nullable=False))
    op.add_column("agencies", sa.Column("subscription_status", sa.String(50), server_default="active", nullable=False))
    op.add_column("agencies", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("agencies", "trial_ends_at")
    op.drop_column("agencies", "subscription_status")
    op.drop_column("agencies", "subscription_plan")
    op.drop_column("agencies", "razorpay_customer_id")
