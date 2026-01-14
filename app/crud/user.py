from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.utils.auth import get_password_hash, verify_password
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_phone(db: Session, phone_number: str) -> Optional[User]:
    """Get user by phone number."""
    return db.query(User).filter(User.phone_number == phone_number).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_telegram_id(db: Session, telegram_id: str) -> Optional[User]:
    """Get user by Telegram ID."""
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """Get list of users with filters and pagination."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def get_users_count(
    db: Session,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> int:
    """Get total count of users."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.count()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user (web registration with username/password)."""
    try:
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        db_user = User(
            phone_number=user.phone_number,
            username=user.username,
            telegram_id=getattr(user, 'telegram_id', None),
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role,
            current_lang=user.current_lang
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created user: {db_user.username} with role {db_user.role}")
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create user: {e}")
        raise DatabaseError("User with this phone number, username, or telegram_id already exists")


def create_telegram_user(db: Session, phone_number: str, telegram_id: str, full_name: Optional[str] = None, current_lang: str = "ru") -> User:
    """Create new user from Telegram bot (no username/password required)."""
    from app.models.user import Language
    
    try:
        # Map language string to enum
        lang_map = {"uz": Language.UZBEK, "ru": Language.RUSSIAN, "en": Language.ENGLISH}
        lang = lang_map.get(current_lang, Language.RUSSIAN)
        
        db_user = User(
            phone_number=phone_number,
            telegram_id=telegram_id,
            full_name=full_name,
            role=UserRole.USER,
            current_lang=lang,
            is_active=False  # Inactive until admin activates
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created Telegram user: {telegram_id} - awaiting activation")
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create Telegram user: {e}")
        raise DatabaseError("User with this phone number or telegram_id already exists")


def update_user(
    db: Session,
    user_id: UUID,
    user_update: UserUpdate
) -> Optional[User]:
    """Update user."""
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    logger.info(f"Updated user: {db_user.username}")
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password."""
    user = get_user_by_username(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Delete user."""
    db_user = get_user(db, user_id)
    
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    logger.info(f"Deleted user: {db_user.username}")
    return True
