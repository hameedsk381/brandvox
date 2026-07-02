import logging
from datetime import datetime, timedelta, timezone
from asyncio import timeout as async_timeout
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.tenant import Location, Client
from app.models.integration import GoogleIntegration
from app.services.google_integration_service import import_google_reviews_for_location

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Simple concurrency guard to prevent overlapping job runs
_sync_in_progress = False

async def sync_google_reviews():
    """Background task to fetch new Google reviews for mapped locations."""
    global _sync_in_progress

    if _sync_in_progress:
        logger.warning("Previous sync still in progress. Skipping this run.")
        return

    _sync_in_progress = True
    started_at = datetime.now(timezone.utc)
    total_synced = 0
    total_skipped_backoff = 0
    total_errors = 0
    total_locations = 0

    logger.info("Running scheduled job: sync_google_reviews")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Location)
                .filter(Location.google_location_id.isnot(None))
                .options(selectinload(Location.client).selectinload(Client.agency))
            )
            locations = result.scalars().all()
            total_locations = len(locations)

            now = datetime.utcnow()

            for location in locations:
                integ_res = await db.execute(
                    select(GoogleIntegration).filter(GoogleIntegration.client_id == location.client_id)
                )
                integration = integ_res.scalars().first()

                if not integration:
                    logger.warning("No Google integration found for client %s", location.client_id)
                    continue

                # Skip locations in exponential backoff
                if integration.next_sync_at and integration.next_sync_at.tzinfo is None:
                    next_sync = integration.next_sync_at.replace(tzinfo=timezone.utc)
                elif integration.next_sync_at:
                    next_sync = integration.next_sync_at
                else:
                    next_sync = None

                if next_sync and next_sync > now:
                    logger.info(
                        "Skipping location %s (next_sync_at=%s, failures=%s)",
                        location.id, integration.next_sync_at, integration.sync_failures,
                    )
                    total_skipped_backoff += 1
                    continue

                try:
                    async with async_timeout(120):
                        result = await import_google_reviews_for_location(db, location, integration, location.client.agency)
                        total_synced += result.get("imported_reviews", 0)
                        logger.info(
                            "Synced Google reviews for %s: imported=%s skipped=%s",
                            location.google_location_id,
                            result["imported_reviews"],
                            result["skipped_reviews"],
                        )
                except ValueError as exc:
                    total_errors += 1
                    logger.warning("Sync failed for location %s: %s", location.id, exc)
                except TimeoutError:
                    total_errors += 1
                    logger.error("Sync timed out for location %s", location.id)
    finally:
        _sync_in_progress = False
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
            "Sync cycle complete: %d locations, %d synced, %d skipped (backoff), %d errors, %.1fs",
            total_locations, total_synced, total_skipped_backoff, total_errors, elapsed,
        )

async def process_scheduled_reports():
    """Generate and persist scheduled reports that are due."""
    from app.models.scheduled_report import ScheduledReport
    from app.services.report_service import generate_pdf_report, generate_excel_report, generate_pptx_report

    logger.info("Checking for due scheduled reports...")
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(ScheduledReport).filter(
                ScheduledReport.is_active == True,
                ScheduledReport.next_run_at <= now,
            )
        )
        due_reports = result.scalars().all()

        if not due_reports:
            logger.info("No scheduled reports due.")
            return

        for report in due_reports:
            try:
                agency_id = report.agency_id
                client_id = report.client_id
                location_id = report.location_id
                report_type = report.report_type

                if report.format == "xlsx":
                    file_bytes = await generate_excel_report(db, agency_id, client_id, location_id, report_type)
                elif report.format == "pptx":
                    file_bytes = await generate_pptx_report(db, agency_id, client_id, location_id, report_type)
                else:
                    file_bytes = await generate_pdf_report(db, agency_id, client_id, location_id, report_type)

                logger.info(
                    "Generated scheduled report '%s' (%s, %s): %d bytes",
                    report.name, report.format, report_type, len(file_bytes),
                )

                # Update last_sent_at and calculate next_run_at
                report.last_sent_at = now

                # Simple cron-like: advance based on report_type
                if report.report_type == "weekly":
                    report.next_run_at = now + timedelta(days=7)
                elif report.report_type == "quarterly":
                    report.next_run_at = now + timedelta(days=90)
                else:
                    report.next_run_at = now + timedelta(days=30)

                await db.commit()

            except Exception as exc:
                logger.error("Failed to process scheduled report %s: %s", report.id, exc)


async def cleanup_old_audit_logs():
    """Delete audit logs older than the configured retention period."""
    from app.config import get_settings
    from app.models.audit import AuditLog

    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
    logger.info("Purging audit logs older than %s (%d days)", cutoff, settings.AUDIT_LOG_RETENTION_DAYS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AuditLog).filter(AuditLog.created_at < cutoff)
        )
        old_logs = result.scalars().all()
        count = len(old_logs)
        for log in old_logs:
            await db.delete(log)
        await db.commit()
        logger.info("Purged %d audit log records", count)

async def retry_webhook_deliveries():
    from app.services.webhook_service import retry_failed_deliveries
    await retry_failed_deliveries()

def start_scheduler():
    scheduler.add_job(sync_google_reviews, "interval", hours=1)
    scheduler.add_job(process_scheduled_reports, "interval", minutes=5)
    scheduler.add_job(cleanup_old_audit_logs, "interval", days=1)
    scheduler.add_job(retry_webhook_deliveries, "interval", minutes=5)
    scheduler.start()
    logger.info("Scheduler started successfully")

async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
