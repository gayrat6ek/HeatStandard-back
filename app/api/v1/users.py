from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from app.models.user import User, UserRole
from app.crud import user as crud_user
from app.api.dependencies import get_current_admin_user, get_current_user


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=UserList)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    telegram_id: Optional[str] = Query(None, description="Filter by telegram ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all users (Admin only).
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **role**: Filter by user role
    - **is_active**: Filter by active status
    - **telegram_id**: Filter by Telegram user ID
    """
    users = crud_user.get_users(
        db=db,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
        telegram_id=telegram_id
    )
    total = crud_user.get_users_count(
        db=db, 
        role=role, 
        is_active=is_active,
        telegram_id=telegram_id
    )
    
    return UserList(total=total, items=users)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user


@router.get("/telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user by Telegram ID.
    
    Useful for Telegram bot to check if user exists and get their info.
    """
    user = crud_user.get_user_by_telegram_id(db=db, telegram_id=telegram_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (Admin only)."""
    user = crud_user.get_user(db=db, user_id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create new user (Admin only).
    
    Only admins can create new users and assign roles.
    """
    # Check if user already exists
    existing_user = crud_user.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_phone = crud_user.get_user_by_phone(db, user.phone_number)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    return crud_user.create_user(db=db, user=user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (Admin only)."""
    # Get original user to check status change
    original_user = crud_user.get_user(db=db, user_id=user_id)
    if not original_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if activating
    was_inactive = not original_user.is_active
    updated_user = crud_user.update_user(db=db, user_id=user_id, user_update=user_update)
    
    # Send notification if activated
    if was_inactive and updated_user.is_active and updated_user.telegram_id:
        from app.utils.telegram import send_telegram_message
        
        # Determine language for message
        lang = updated_user.current_lang.value if hasattr(updated_user, 'current_lang') and updated_user.current_lang else 'ru'
        
        messages = {
            'uz': "Sizning hisobingiz faollashtirildi! \nEndi buyurtma berishingiz mumkin. \n/start ni bosing.",
            'ru': "Ваш аккаунт активирован! \nТеперь вы можете делать заказы. \nНажмите /start.",
            'en': "Your account has been activated! \nYou can now place orders. \nPress /start."
        }
        text = messages.get(lang, messages['ru'])
        
        # Send in background to avoid blocking the response
        background_tasks.add_task(send_telegram_message, updated_user.telegram_id, text)
    
    return updated_user


@router.put("/me/profile", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Users can update their own profile but cannot change their role.
    """
    # Prevent users from changing their own role
    if user_update.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    updated_user = crud_user.update_user(
        db=db,
        user_id=current_user.id,
        user_update=user_update
    )
    
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (Admin only)."""
    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = crud_user.delete_user(db=db, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}
