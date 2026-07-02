import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.tenant import Location, Client
from app.models.integration import GoogleIntegration
from app.services.google_integration_service import import_google_reviews_for_location

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def sync_google_reviews():
    """Background task to fetch new Google reviews for mapped locations."""
    logger.info("Running scheduled job: sync_google_reviews")
    async with AsyncSessionLocal() as db:
        # Find all locations with a google_location_id
        result = await db.execute(
            select(Location)
            .filter(Location.google_location_id.isnot(None))
            .options(selectinload(Location.client).selectinload(Client.agency))
        )
        locations = result.scalars().all()
        
        for location in locations:
            # Find the integration for the client
            integ_res = await db.execute(
                select(GoogleIntegration).filter(GoogleIntegration.client_id == location.client_id)
            )
            integration = integ_res.scalars().first()
            
            if not integration:
                logger.warning(f"No Google integration found for client {location.client_id}")
                continue

            try:
                result = await import_google_reviews_for_location(db, location, integration, location.client.agency)
                logger.info(
                    "Synced Google reviews for %s: imported=%s skipped=%s",
                    location.google_location_id,
                    result["imported_reviews"],
                    result["skipped_reviews"],
                )
            except ValueError as exc:
                logger.warning("Skipping Google sync for location %s: %s", location.id, exc)

def start_scheduler():
    scheduler.add_job(sync_google_reviews, "interval", hours=1)
    scheduler.start()
    logger.info("Scheduler started successfully")
