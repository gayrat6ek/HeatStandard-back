from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import logging

from app.models.terminal_group import TerminalGroup
from app.schemas.terminal_group import TerminalGroupCreate, TerminalGroupUpdate
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_terminal_group(db: Session, terminal_group_id: UUID) -> Optional[TerminalGroup]:
    """Get terminal group by ID."""
    return db.query(TerminalGroup).filter(TerminalGroup.id == terminal_group_id).first()


def get_terminal_group_by_iiko_id(db: Session, iiko_id: str) -> Optional[TerminalGroup]:
    """Get terminal group by iiko ID."""
    return db.query(TerminalGroup).filter(TerminalGroup.iiko_id == iiko_id).first()


def get_terminal_groups(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = None,
    is_active: Optional[bool] = None
) -> List[TerminalGroup]:
    """Get list of terminal groups with filters and pagination."""
    query = db.query(TerminalGroup)
    
    if organization_id:
        query = query.filter(TerminalGroup.organization_id == organization_id)
    
    if is_active is not None:
        query = query.filter(TerminalGroup.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def get_terminal_groups_count(
    db: Session,
    organization_id: Optional[UUID] = None,
    is_active: Optional[bool] = None
) -> int:
    """Get total count of terminal groups."""
    query = db.query(TerminalGroup)
    
    if organization_id:
        query = query.filter(TerminalGroup.organization_id == organization_id)
    
    if is_active is not None:
        query = query.filter(TerminalGroup.is_active == is_active)
    
    return query.count()


def create_terminal_group(db: Session, terminal_group: TerminalGroupCreate) -> TerminalGroup:
    """Create new terminal group."""
    try:
        db_terminal_group = TerminalGroup(**terminal_group.model_dump())
        db.add(db_terminal_group)
        db.commit()
        db.refresh(db_terminal_group)
        logger.info(f"Created terminal group: {db_terminal_group.name}")
        return db_terminal_group
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create terminal group: {e}")
        raise DatabaseError(f"Terminal group with iiko_id already exists")


def update_terminal_group(
    db: Session,
    terminal_group_id: UUID,
    terminal_group_update: TerminalGroupUpdate
) -> Optional[TerminalGroup]:
    """Update terminal group."""
    db_terminal_group = get_terminal_group(db, terminal_group_id)
    
    if not db_terminal_group:
        return None
    
    update_data = terminal_group_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_terminal_group, field, value)
    
    db.commit()
    db.refresh(db_terminal_group)
    logger.info(f"Updated terminal group: {db_terminal_group.name}")
    return db_terminal_group


def upsert_terminal_group(db: Session, terminal_group_data: dict) -> TerminalGroup:
    """Create or update terminal group based on iiko_id."""
    existing = get_terminal_group_by_iiko_id(db, terminal_group_data["iiko_id"])
    
    if existing:
        # Update existing
        for key, value in terminal_group_data.items():
            if key != "id" and hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        terminal_group_create = TerminalGroupCreate(**terminal_group_data)
        return create_terminal_group(db, terminal_group_create)


def delete_terminal_group(db: Session, terminal_group_id: UUID) -> bool:
    """Delete terminal group."""
    db_terminal_group = get_terminal_group(db, terminal_group_id)
    
    if not db_terminal_group:
        return False
    
    db.delete(db_terminal_group)
    db.commit()
    logger.info(f"Deleted terminal group: {db_terminal_group.name}")
    return True
