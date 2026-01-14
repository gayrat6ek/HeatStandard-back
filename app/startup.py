"""Startup script to initialize the application."""
import asyncio
from app.database import SessionLocal
from app.crud.user import create_user, get_user_by_username
from app.schemas.user import UserCreate
from app.models.user import UserRole
import logging

logger = logging.getLogger(__name__)


async def create_default_admin():
    """Create default admin user if it doesn't exist."""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = get_user_by_username(db, "admin")
        
        if existing_admin:
            logger.info("Admin user already exists")
            return
        
        # Create default admin user
        admin_user = UserCreate(
            email="admin@iiko.local",
            username="admin",
            full_name="System Administrator",
            password="admin123",  # CHANGE THIS IN PRODUCTION!
            role=UserRole.ADMIN
        )
        
        user = create_user(db, admin_user)
        logger.info(f"✓ Default admin user created: {user.username}")
        logger.warning("⚠️  Default password is 'admin123' - PLEASE CHANGE IT!")
        
    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")
    finally:
        db.close()


async def initialize_app():
    """Initialize application on startup."""
    logger.info("Initializing application...")
    
    # Create default admin user
    await create_default_admin()
    
    logger.info("Application initialization complete")


if __name__ == "__main__":
    asyncio.run(initialize_app())
