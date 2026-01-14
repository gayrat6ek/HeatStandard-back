"""Application lifespan management for startup and shutdown events."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import SessionLocal
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate
from app.models.user import UserRole, Language
from app.services.scheduler import start_scheduler, stop_scheduler, sync_organizations_from_iiko


logger = logging.getLogger(__name__)


async def create_superadmin():
    """Create default superadmin if it doesn't exist."""
    db = SessionLocal()
    
    try:
        existing_admin = get_user_by_username(db, "admin")
        
        if existing_admin:
            logger.info("Superadmin already exists")
            return
        
        admin_user = UserCreate(
            phone_number="+998900000000",
            username="admin",
            full_name="Super Administrator",
            password="admin123",
            role=UserRole.ADMIN,
            current_lang=Language.RUSSIAN
        )
        
        user = create_user(db, admin_user)
        logger.info(f"✓ Superadmin created: {user.username}")
        logger.warning("⚠️ Default password is 'admin123' - CHANGE IT!")
        
    except Exception as e:
        logger.error(f"Failed to create superadmin: {e}")
    finally:
        db.close()


async def initial_iiko_sync():
    """Perform initial sync from iiko on startup."""
    logger.info("Performing initial iiko sync...")
    try:
        await sync_organizations_from_iiko()
    except Exception as e:
        logger.error(f"Initial iiko sync failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Application starting up...")
    
    # Create superadmin
    await create_superadmin()
    
    # Initial iiko sync
    await initial_iiko_sync()
    
    # Start scheduler for daily syncs
    start_scheduler()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    stop_scheduler()
    logger.info("Application shutdown complete")
