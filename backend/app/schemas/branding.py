from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class BrandingConfigBase(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    accent_color: str = "#06b6d4"
    font_family: str = "Inter"
    dark_mode_default: bool = True
    sidebar_style: str = "modern"
    login_bg_image: Optional[str] = None
    custom_css: Optional[str] = None

class BrandingConfigCreate(BrandingConfigBase):
    agency_id: UUID

class BrandingConfigUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    dark_mode_default: Optional[bool] = None
    sidebar_style: Optional[str] = None
    login_bg_image: Optional[str] = None
    custom_css: Optional[str] = None

class BrandingConfigResponse(BrandingConfigBase):
    id: UUID
    agency_id: UUID

    class Config:
        from_attributes = True
