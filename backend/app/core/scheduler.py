import logging
from datetime import datetime, timedelta, timezone
from asyncio import timeout as async_timeout
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.tenant import Location, Client
from app.models.integration import GoogleIntegration
from app.services.google_integration_service import import_google_reviews_for_location, mark_google_sync_status

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

            # Must be timezone-aware: next_sync below is normalized to UTC-aware,
            # and comparing aware to naive raises TypeError.
            now = datetime.now(timezone.utc)

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
                    # Record the failure so backoff applies; otherwise a
                    # persistently slow tenant is retried at full rate forever.
                    try:
                        await db.rollback()
                        await mark_google_sync_status(db, integration, "failed", "Sync timed out after 120s")
                    except Exception as mark_exc:
                        logger.error("Could not record timeout for location %s: %s", location.id, mark_exc)
    finally:
        _sync_in_progress = False
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
            "Sync cycle complete: %d locations, %d synced, %d skipped (backoff), %d errors, %.1fs",
            total_locations, total_synced, total_skipped_backoff, total_errors, elapsed,
        )

REPORT_MIME_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
}


async def process_scheduled_reports():
    """Generate due scheduled reports and email them to their recipients."""
    from app.models.scheduled_report import ScheduledReport
    from app.services.notification_service import send_email
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

                # Deliver to recipients; last_sent_at is only stamped when
                # every recipient send succeeded (it must not lie).
                recipients = report.recipients or []
                fmt = report.format if report.format in REPORT_MIME_TYPES else "pdf"
                filename = f"{report.name}_{now.strftime('%Y-%m-%d')}.{fmt}"
                all_sent = True
                for recipient in recipients:
                    sent = await send_email(
                        to=recipient,
                        subject=f"Scheduled report: {report.name}",
                        content=f"<p>Your scheduled {report_type} report <b>{report.name}</b> is attached.</p>",
                        attachment=file_bytes,
                        attachment_filename=filename,
                        attachment_mime_type=REPORT_MIME_TYPES[fmt],
                    )
                    if not sent:
                        all_sent = False
                        logger.error("Failed to send report '%s' to %s", report.name, recipient)

                if not recipients:
                    logger.warning("Scheduled report '%s' has no recipients; generated but not delivered", report.name)

                if all_sent and recipients:
                    report.last_sent_at = now

                # Advance the schedule regardless of delivery outcome so a dead
                # mailbox can't make the job re-fire every 5 minutes.
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

    from sqlalchemy import delete as sa_delete

    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
    logger.info("Purging audit logs older than %s (%d days)", cutoff, settings.AUDIT_LOG_RETENTION_DAYS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(sa_delete(AuditLog).where(AuditLog.created_at < cutoff))
        await db.commit()
        logger.info("Purged %d audit log records", result.rowcount)

async def retry_webhook_deliveries():
    from app.services.webhook_service import retry_failed_deliveries
    await retry_failed_deliveries()

# Session-scoped PostgreSQL advisory lock: only the process holding it runs the
# scheduler, so multiple workers/replicas don't duplicate jobs. The connection
# must stay open for the lifetime of the process to keep the lock.
SCHEDULER_LOCK_KEY = 0x5245504F  # arbitrary app-wide constant ("REPO")
_scheduler_lock_conn = None


async def _try_acquire_scheduler_lock() -> bool:
    global _scheduler_lock_conn
    from sqlalchemy import text
    from app.database import engine

    conn = await engine.connect()
    try:
        result = await conn.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": SCHEDULER_LOCK_KEY}
        )
        acquired = bool(result.scalar())
    except Exception:
        await conn.close()
        raise
    if acquired:
        _scheduler_lock_conn = conn
        return True
    await conn.close()
    return False


async def start_scheduler():
    from app.config import get_settings

    if not get_settings().ENABLE_SCHEDULER:
        logger.info("Scheduler disabled via ENABLE_SCHEDULER=false")
        return

    try:
        acquired = await _try_acquire_scheduler_lock()
    except Exception as exc:
        logger.error("Could not check scheduler advisory lock: %s. Starting scheduler anyway.", exc)
        acquired = True

    if not acquired:
        logger.info("Another process holds the scheduler lock; not starting scheduler in this process")
        return

    scheduler.add_job(sync_google_reviews, "interval", hours=1)
    scheduler.add_job(process_scheduled_reports, "interval", minutes=5)
    scheduler.add_job(cleanup_old_audit_logs, "interval", days=1)
    scheduler.add_job(retry_webhook_deliveries, "interval", minutes=5)
    scheduler.start()
    logger.info("Scheduler started successfully")

async def stop_scheduler():
    global _scheduler_lock_conn
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    if _scheduler_lock_conn is not None:
        try:
            from sqlalchemy import text
            await _scheduler_lock_conn.execute(
                text("SELECT pg_advisory_unlock(:key)"), {"key": SCHEDULER_LOCK_KEY}
            )
        finally:
            await _scheduler_lock_conn.close()
            _scheduler_lock_conn = None
