import logging
from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    db_status = "disconnected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        logger.warning("Health check DB connection failed: %s", e)

    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
    }
