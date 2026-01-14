from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import logging

from app.models.section import Section
from app.schemas.section import SectionCreate, SectionUpdate
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_section(db: Session, section_id: UUID) -> Optional[Section]:
    """Get section by ID."""
    return db.query(Section).filter(Section.id == section_id).first()


def get_section_by_iiko_id(db: Session, iiko_id: str) -> Optional[Section]:
    """Get section by iiko ID."""
    return db.query(Section).filter(Section.iiko_id == iiko_id).first()


def get_sections(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = None,
    is_active: Optional[bool] = None
) -> List[Section]:
    """Get list of sections with filters and pagination."""
    query = db.query(Section)
    
    if organization_id:
        query = query.filter(Section.organization_id == organization_id)
    
    if is_active is not None:
        query = query.filter(Section.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def get_sections_count(
    db: Session,
    organization_id: Optional[UUID] = None,
    is_active: Optional[bool] = None
) -> int:
    """Get total count of sections."""
    query = db.query(Section)
    
    if organization_id:
        query = query.filter(Section.organization_id == organization_id)
    
    if is_active is not None:
        query = query.filter(Section.is_active == is_active)
    
    return query.count()


def create_section(db: Session, section: SectionCreate) -> Section:
    """Create new section."""
    try:
        db_section = Section(**section.model_dump())
        db.add(db_section)
        db.commit()
        db.refresh(db_section)
        logger.info(f"Created section: {db_section.name}")
        return db_section
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create section: {e}")
        raise DatabaseError(f"Section with iiko_id already exists")


def update_section(
    db: Session,
    section_id: UUID,
    section_update: SectionUpdate
) -> Optional[Section]:
    """Update section."""
    db_section = get_section(db, section_id)
    
    if not db_section:
        return None
    
    update_data = section_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_section, field, value)
    
    db.commit()
    db.refresh(db_section)
    logger.info(f"Updated section: {db_section.name}")
    return db_section


def upsert_section(db: Session, section_data: dict) -> Section:
    """Create or update section based on iiko_id."""
    existing = get_section_by_iiko_id(db, section_data["iiko_id"])
    
    if existing:
        # Update existing
        for key, value in section_data.items():
            if key != "id" and hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        section_create = SectionCreate(**section_data)
        return create_section(db, section_create)


def delete_section(db: Session, section_id: UUID) -> bool:
    """Delete section."""
    db_section = get_section(db, section_id)
    
    if not db_section:
        return False
    
    db.delete(db_section)
    db.commit()
    logger.info(f"Deleted section: {db_section.name}")
    return True
