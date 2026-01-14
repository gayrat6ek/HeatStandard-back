from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"


class Language(str, enum.Enum):
    """Supported languages."""
    UZBEK = "uz"
    RUSSIAN = "ru"
    ENGLISH = "en"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=True, index=True)  # Optional for bot users
    telegram_id = Column(String, unique=True, nullable=True, index=True)  # Telegram user ID
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Optional for bot users
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    current_lang = Column(SQLEnum(Language), default=Language.RUSSIAN, nullable=False)
    is_active = Column(Boolean, default=False)  # Users inactive until admin activates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, telegram_id={self.telegram_id})>"
