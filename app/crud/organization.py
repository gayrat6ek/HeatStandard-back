from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import logging

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_organization(db: Session, organization_id: UUID) -> Optional[Organization]:
    """Get organization by ID."""
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_iiko_id(db: Session, iiko_id: str) -> Optional[Organization]:
    """Get organization by iiko ID."""
    return db.query(Organization).filter(Organization.iiko_id == iiko_id).first()


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[Organization]:
    """Get list of organizations with pagination."""
    query = db.query(Organization)
    
    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def get_organizations_count(db: Session, is_active: Optional[bool] = None) -> int:
    """Get total count of organizations."""
    query = db.query(Organization)
    
    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)
    
    return query.count()


def create_organization(db: Session, organization: OrganizationCreate) -> Organization:
    """Create new organization."""
    try:
        db_organization = Organization(**organization.model_dump())
        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
        logger.info(f"Created organization: {db_organization.name}")
        return db_organization
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create organization: {e}")
        raise DatabaseError(f"Organization with iiko_id already exists")


def update_organization(
    db: Session,
    organization_id: UUID,
    organization_update: OrganizationUpdate
) -> Optional[Organization]:
    """Update organization."""
    db_organization = get_organization(db, organization_id)
    
    if not db_organization:
        return None
    
    update_data = organization_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_organization, field, value)
    
    db.commit()
    db.refresh(db_organization)
    logger.info(f"Updated organization: {db_organization.name}")
    return db_organization


def upsert_organization(db: Session, organization_data: dict) -> Organization:
    """Create or update organization based on iiko_id."""
    existing = get_organization_by_iiko_id(db, organization_data["iiko_id"])
    
    if existing:
        # Update existing
        for key, value in organization_data.items():
            if key != "id" and hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        org_create = OrganizationCreate(**organization_data)
        return create_organization(db, org_create)


def delete_organization(db: Session, organization_id: UUID) -> bool:
    """Delete organization."""
    db_organization = get_organization(db, organization_id)
    
    if not db_organization:
        return False
    
    db.delete(db_organization)
    db.commit()
    logger.info(f"Deleted organization: {db_organization.name}")
    return True
