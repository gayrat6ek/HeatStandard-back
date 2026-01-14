from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, Language


class UserBase(BaseModel):
    """Base user schema."""
    phone_number: str = Field(min_length=9, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    telegram_id: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating user via web (requires username and password)."""
    username: str = Field(min_length=3, max_length=50)  # Required for web registration
    password: str = Field(min_length=6)
    role: UserRole = UserRole.USER
    current_lang: Language = Language.RUSSIAN


class TelegramUserCreate(BaseModel):
    """Schema for creating user via Telegram bot (no username/password required)."""
    phone_number: str = Field(min_length=9, max_length=20)
    telegram_id: str = Field(min_length=1)  # Required for bot registration
    full_name: Optional[str] = None
    current_lang: Language = Language.RUSSIAN


class UserUpdate(BaseModel):
    """Schema for updating user."""
    phone_number: Optional[str] = Field(None, min_length=9, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    telegram_id: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    current_lang: Optional[Language] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    phone_number: str
    username: Optional[str]
    telegram_id: Optional[str]
    full_name: Optional[str]
    role: UserRole
    current_lang: Language
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    """Schema for user list response."""
    total: int
    items: list[UserResponse]


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Schema for login request (web users with username/password)."""
    username: str
    password: str


class TelegramLoginRequest(BaseModel):
    """Schema for Telegram bot login (using telegram_id)."""
    telegram_id: str
