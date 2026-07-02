import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import get_settings
from app.database import engine, Base

# Import all models to ensure they are registered
from app.models import *

# Routers
from app.api.auth import router as auth_router
from app.api.tenants import router as tenants_router
from app.api.reviews import router as reviews_router
from app.api.replies import router as replies_router
from app.api.analytics import router as analytics_router
from app.api.brand_voice import router as brand_voice_router
from app.api.branding import router as branding_router
from app.api.smart_rules import router as smart_rules_router
from app.api.reports import router as reports_router
from app.api.users import router as users_router
from app.api.google_auth import router as google_auth_router
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.competitors import router as competitors_router
from app.api.alerts import router as alerts_router
from app.api.forecasting import router as forecasting_router
from app.api.billing import router as billing_router
from app.api.audit import router as audit_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="ReputationOS AI API",
    description="AI-Powered Brand Reputation Intelligence Platform API",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# CORS configuration
origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "status_code": 422,
            "errors": exc.errors(),
        },
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "status_code": 422,
            "errors": exc.errors(),
        },
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource conflict", "status_code": 409},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500},
    )

# Register routers under prefix
api_prefix = "/api"
app.include_router(health_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)
app.include_router(tenants_router, prefix=api_prefix)
app.include_router(reviews_router, prefix=api_prefix)
app.include_router(replies_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)
app.include_router(brand_voice_router, prefix=api_prefix)
app.include_router(branding_router, prefix=api_prefix)
app.include_router(smart_rules_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(google_auth_router, prefix=api_prefix)
app.include_router(chat_router, prefix=api_prefix)
app.include_router(competitors_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(forecasting_router, prefix=api_prefix)
app.include_router(billing_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)

@app.on_event("startup")
async def on_startup():
    # Environment validation
    _validate_environment()

    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")
    
    # Start scheduler
    from app.core.scheduler import start_scheduler
    start_scheduler()


def _validate_environment():
    if settings.JWT_SECRET == "change-me-in-production-use-a-long-random-string":
        logger.warning(
            "INSECURE: JWT_SECRET is still set to the default value. "
            "Generate a strong random secret in production."
        )

    if not settings.JWT_SECRET:
        logger.warning("JWT_SECRET is not set. Authentication will be insecure.")

    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL is not set. The application may not function correctly.")
    else:
        if "postgres" not in settings.DATABASE_URL:
            logger.warning(
                "DATABASE_URL does not appear to point to a PostgreSQL database: %s",
                settings.DATABASE_URL.split(":")[0] if ":" in settings.DATABASE_URL else "unknown",
            )
