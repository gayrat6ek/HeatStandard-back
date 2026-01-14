"""Script to create the first admin user."""
import asyncio
from app.database import SessionLocal
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import UserRole


def create_admin():
    """Create admin user."""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        from app.crud.user import get_user_by_username
        existing_admin = get_user_by_username(db, "admin")
        
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = UserCreate(
            email="admin@example.com",
            username="admin",
            full_name="System Administrator",
            password="admin123",
            role=UserRole.ADMIN
        )
        
        user = create_user(db, admin_user)
        print(f"✓ Admin user created successfully!")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role.value}")
        print(f"\n⚠️  Default password: admin123")
        print(f"⚠️  Please change this password immediately!")
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
