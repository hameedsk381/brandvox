from sqlalchemy import Column, String, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid as UUID
from app.database import Base
from app.models.base import BaseMixin

class Agency(Base, BaseMixin):
    __tablename__ = "agencies"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    settings = Column(JSON, default=dict, nullable=False)
    google_oauth_client_id = Column(String(255), nullable=True)
    google_oauth_client_secret = Column(String(255), nullable=True)
    
    # Billing & Subscriptions
    razorpay_customer_id = Column(String(255), nullable=True)
    subscription_plan = Column(String(50), default="trial", nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)

    # Relationships
    branding_config = relationship("BrandingConfig", back_populates="agency", uselist=False, cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="agency", cascade="all, delete-orphan")
    users = relationship("User", back_populates="agency")

class BrandingConfig(Base, BaseMixin):
    __tablename__ = "branding_configs"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    logo_url = Column(String(1024), nullable=True)
    favicon_url = Column(String(1024), nullable=True)
    primary_color = Column(String(7), default="#6366f1", nullable=False) # Hex color
    secondary_color = Column(String(7), default="#8b5cf6", nullable=False)
    accent_color = Column(String(7), default="#06b6d4", nullable=False)
    font_family = Column(String(100), default="Inter", nullable=False)
    dark_mode_default = Column(Boolean, default=True, nullable=False)
    sidebar_style = Column(String(50), default="modern", nullable=False)
    login_bg_image = Column(String(1024), nullable=True)
    custom_css = Column(String, nullable=True)

    # Relationships
    agency = relationship("Agency", back_populates="branding_config")

class Client(Base, BaseMixin):
    __tablename__ = "clients"

    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    settings = Column(JSON, default=dict, nullable=False)

    # Relationships
    agency = relationship("Agency", back_populates="clients")
    locations = relationship("Location", back_populates="client", cascade="all, delete-orphan")
    brand_voice = relationship("BrandVoiceProfile", back_populates="client", uselist=False, cascade="all, delete-orphan")
    users = relationship("User", back_populates="client")

class Location(Base, BaseMixin):
    __tablename__ = "locations"

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String, nullable=True)
    google_place_id = Column(String(255), nullable=True)
    google_location_id = Column(String(255), nullable=True)
    last_sync_time = Column(DateTime, nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Relationships
    client = relationship("Client", back_populates="locations")
    reviews = relationship("Review", back_populates="location", cascade="all, delete-orphan")
    reputation_scores = relationship("ReputationScore", back_populates="location", cascade="all, delete-orphan")
    smart_rules = relationship("SmartRule", back_populates="location", cascade="all, delete-orphan")
    users = relationship("User", back_populates="location")
