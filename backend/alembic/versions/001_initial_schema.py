"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("settings", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "branding_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agencies.id", ondelete="CASCADE")),
        sa.Column("company_name", sa.String(255)),
        sa.Column("logo_url", sa.Text),
        sa.Column("favicon_url", sa.Text),
        sa.Column("primary_color", sa.String(7), server_default="#6366f1"),
        sa.Column("secondary_color", sa.String(7), server_default="#8b5cf6"),
        sa.Column("accent_color", sa.String(7), server_default="#06b6d4"),
        sa.Column("font_family", sa.String(100), server_default="Inter"),
        sa.Column("dark_mode_default", sa.Boolean, server_default=sa.text("true")),
        sa.Column("sidebar_style", sa.String(20), server_default="modern"),
        sa.Column("login_bg_image", sa.Text),
        sa.Column("custom_css", sa.Text),
        sa.UniqueConstraint("agency_id"),
    )
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agency_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agencies.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100)),
        sa.Column("settings", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("google_place_id", sa.String(255)),
        sa.Column("timezone", sa.String(50), server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="read_only"),
        sa.Column("agency_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agencies.id")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(50), server_default="google"),
        sa.Column("source_review_id", sa.String(255)),
        sa.Column("author_name", sa.String(255)),
        sa.Column("author_image_url", sa.Text),
        sa.Column("rating", sa.Integer, sa.CheckConstraint("rating BETWEEN 1 AND 5")),
        sa.Column("text", sa.Text),
        sa.Column("review_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("source", "source_review_id"),
    )
    op.create_table(
        "review_replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("generated_by", sa.String(20), server_default="ai"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "sentiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), unique=True),
        sa.Column("sentiment", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("emotions", postgresql.ARRAY(sa.Text)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "topic_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE")),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("sub_topic", sa.String(100)),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "reputation_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="CASCADE")),
        sa.Column("score_date", sa.Date, nullable=False),
        sa.Column("overall_score", sa.Float),
        sa.Column("avg_rating", sa.Float),
        sa.Column("review_volume", sa.Integer),
        sa.Column("sentiment_score", sa.Float),
        sa.Column("response_rate", sa.Float),
        sa.Column("components", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("location_id", "score_date"),
    )
    op.create_table(
        "brand_voice_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE")),
        sa.Column("tone", sa.String(50), server_default="professional"),
        sa.Column("vocabulary_notes", sa.Text),
        sa.Column("greeting_style", sa.Text),
        sa.Column("closing_style", sa.Text),
        sa.Column("example_replies", postgresql.ARRAY(sa.Text)),
        sa.Column("personality_traits", postgresql.ARRAY(sa.Text)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id"),
    )
    op.create_table(
        "smart_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="CASCADE")),
        sa.Column("min_rating", sa.Integer, nullable=False),
        sa.Column("max_rating", sa.Integer, nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("notify_roles", postgresql.ARRAY(sa.Text)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("smart_rules")
    op.drop_table("brand_voice_profiles")
    op.drop_table("reputation_scores")
    op.drop_table("topic_results")
    op.drop_table("sentiment_results")
    op.drop_table("review_replies")
    op.drop_table("reviews")
    op.drop_table("users")
    op.drop_table("locations")
    op.drop_table("clients")
    op.drop_table("branding_configs")
    op.drop_table("agencies")
