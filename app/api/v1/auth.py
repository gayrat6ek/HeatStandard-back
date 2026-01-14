from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.schemas.user import LoginRequest, Token, UserResponse, UserCreate, TelegramUserCreate, TelegramLoginRequest
from app.crud import user as crud_user
from app.models.user import UserRole
from app.utils.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


class RegisterRequest(UserCreate):
    """Registration request - users can't set their own role."""
    role: UserRole = UserRole.USER  # Always USER for registration


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    New users are inactive by default and need to be activated by an admin
    before they can login and place orders.
    
    - **phone_number**: User's phone number
    - **username**: Unique username
    - **full_name**: User's full name (optional)
    - **password**: Password (min 6 characters)
    """
    # Check if username already exists
    existing_user = crud_user.get_user_by_username(db, register_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if phone already exists
    existing_phone = crud_user.get_user_by_phone(db, register_data.phone_number)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Force role to USER and create with is_active=False
    register_data.role = UserRole.USER
    
    user = crud_user.create_user(db=db, user=register_data)
    logger.info(f"New user registered: {user.username} - awaiting activation")
    
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    - **username**: Username
    - **password**: User password
    """
    # First check if user exists
    user = crud_user.get_user_by_username(db, login_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please wait for admin approval.",
        )
    
    # Authenticate user (verify password)
    authenticated_user = crud_user.authenticate_user(db, login_data.username, login_data.password)
    
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(authenticated_user.id),
            "username": authenticated_user.username,
            "role": authenticated_user.role.value
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {authenticated_user.username} logged in successfully")
    
    return Token(
        access_token=access_token, 
        token_type="bearer",
        user=UserResponse.model_validate(authenticated_user)
    )


@router.post("/telegram/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def telegram_register(
    register_data: TelegramUserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user from Telegram bot.
    
    No username or password required - uses telegram_id for identification.
    New users are inactive by default and need admin activation.
    
    - **phone_number**: User's phone number (required)
    - **telegram_id**: Telegram user ID (required)
    - **full_name**: User's full name (optional)
    - **current_lang**: Preferred language (uz, ru, en)
    """
    # Check if telegram_id already exists
    existing_telegram = crud_user.get_user_by_telegram_id(db, register_data.telegram_id)
    if existing_telegram:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram account already registered"
        )
    
    # Check if phone already exists
    existing_phone = crud_user.get_user_by_phone(db, register_data.phone_number)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    user = crud_user.create_telegram_user(
        db=db,
        phone_number=register_data.phone_number,
        telegram_id=register_data.telegram_id,
        full_name=register_data.full_name,
        current_lang=register_data.current_lang.value
    )
    logger.info(f"New Telegram user registered: {user.telegram_id} - awaiting activation")
    
    return user


@router.post("/telegram/login", response_model=Token)
async def telegram_login(
    login_data: TelegramLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate Telegram user and return JWT token.
    
    Uses telegram_id for identification instead of username/password.
    """
    # Get user by telegram_id
    user = crud_user.get_user_by_telegram_id(db, login_data.telegram_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram account not registered",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please wait for admin approval.",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "telegram_id": user.telegram_id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"Telegram user {user.telegram_id} logged in successfully")
    
    return Token(
        access_token=access_token, 
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should discard the token).
    """
    return {"message": "Successfully logged out"}
