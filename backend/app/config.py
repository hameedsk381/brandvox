import os
import json
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    # Fernet key for encrypting OAuth tokens at rest. Required in production;
    # in development a key is derived from JWT_SECRET.
    ENCRYPTION_KEY: str = ""
    DATABASE_URL: str = Field(default="postgresql+asyncpg://repuser:reppass@postgres:5432/reputationos")
    DATABASE_URL_SYNC: str = Field(default="postgresql://repuser:reppass@postgres:5432/reputationos")
    JWT_SECRET: str = Field(default="change-me-in-production-use-a-long-random-string")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    GROQ_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    # When true, Google API failures fall back to generated mock data instead of
    # raising. Never enable for real customer tenants.
    DEMO_MODE: bool = False
    # Set false on replicas that should not run background jobs. Even when true,
    # a PostgreSQL advisory lock ensures only one process runs the scheduler.
    ENABLE_SCHEDULER: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90
    PASSWORD_RESET_EXPIRY_MINUTES: int = 60
    RATE_LIMIT_PER_WINDOW: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 300
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    # Razorpay webhook signing secret (Dashboard → Webhooks). Falls back to
    # RAZORPAY_KEY_SECRET if empty. Webhooks are rejected without a valid signature.
    RAZORPAY_WEBHOOK_SECRET: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""
    
    # Allow passing CORS origins as a JSON-encoded list or simple comma-separated string
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000", "http://127.0.0.1:3000"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            # Fallback to splitting by comma if it's not a JSON list
            return [x.strip() for x in self.BACKEND_CORS_ORIGINS.split(",") if x.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
