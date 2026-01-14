"""Scheduler service for background tasks using APScheduler."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.services.iiko_service import iiko_service
from app.crud import organization as crud_organization


logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def sync_organizations_from_iiko():
    """Sync organizations from iiko API."""
    logger.info("Starting scheduled iiko organizations sync...")
    db = SessionLocal()
    
    try:
        iiko_organizations = await iiko_service.get_organizations()
        synced_count = 0
        
        for iiko_org in iiko_organizations:
            try:
                org_data = {
                    "iiko_id": iiko_org.get("id"),
                    "name": iiko_org.get("name"),
                    "country": iiko_org.get("country"),
                    "restaurant_address": iiko_org.get("restaurantAddress"),
                    "use_uae_addressing": iiko_org.get("useUaeAddressingSystem", False),
                    "timezone": iiko_org.get("timezone"),
                }
                crud_organization.upsert_organization(db=db, organization_data=org_data)
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing organization {iiko_org.get('id')}: {e}")
        
        logger.info(f"Completed iiko sync: {synced_count} organizations synced")
    except Exception as e:
        logger.error(f"Failed to sync from iiko: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler with configured jobs."""
    # Add daily sync job at 11:00 AM
    scheduler.add_job(
        sync_organizations_from_iiko,
        CronTrigger(hour=11, minute=1),
        id="daily_iiko_sync",
        name="Daily iiko Sync",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with daily iiko sync at 11:00 AM")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
