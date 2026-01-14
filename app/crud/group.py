from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from uuid import UUID
import logging

from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate


logger = logging.getLogger(__name__)


def get_group(db: Session, group_id: UUID) -> Optional[Group]:
    """Get a single group by ID."""
    return db.query(Group).filter(Group.id == group_id).first()


def get_group_by_iiko_id(db: Session, iiko_id: str) -> Optional[Group]:
    """Get a group by iiko ID."""
    return db.query(Group).filter(Group.iiko_id == iiko_id).first()


def get_groups(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    parent_group_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    root_only: bool = False,
    include_inactive: bool = False
) -> List[Group]:
    """
    Get list of groups with optional filtering.
    
    Args:
        parent_group_id: Filter by parent group (None for root groups if root_only=True)
        organization_id: Filter by organization
        root_only: If True, only return groups with no parent
        include_inactive: If True, include inactive groups
    """
    query = db.query(Group)
    
    if not include_inactive:
        query = query.filter(Group.is_active == True)
    
    if organization_id:
        query = query.filter(Group.organization_id == organization_id)
    
    if root_only:
        query = query.filter(Group.parent_group_id == None)
    elif parent_group_id is not None:
        query = query.filter(Group.parent_group_id == parent_group_id)
    
    return query.order_by(Group.order.asc(), Group.name_ru.asc()).offset(skip).limit(limit).all()


def get_groups_count(
    db: Session,
    parent_group_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    root_only: bool = False,
    include_inactive: bool = False
) -> int:
    """Get total count of groups matching filters."""
    query = db.query(Group)
    
    if not include_inactive:
        query = query.filter(Group.is_active == True)
    
    if organization_id:
        query = query.filter(Group.organization_id == organization_id)
    
    if root_only:
        query = query.filter(Group.parent_group_id == None)
    elif parent_group_id is not None:
        query = query.filter(Group.parent_group_id == parent_group_id)
    
    return query.count()


def get_child_groups(db: Session, parent_id: UUID) -> List[Group]:
    """Get all direct children of a group."""
    return db.query(Group).filter(
        and_(Group.parent_group_id == parent_id, Group.is_active == True)
    ).order_by(Group.order.asc()).all()


def create_group(db: Session, group: GroupCreate) -> Group:
    """Create a new group."""
    db_group = Group(
        iiko_id=group.iiko_id,
        name_uz=group.name_uz,
        name_ru=group.name_ru,
        name_en=group.name_en,
        description_uz=group.description_uz,
        description_ru=group.description_ru,
        description_en=group.description_en,
        parent_group_id=group.parent_group_id,
        organization_id=group.organization_id,
        order=group.order,
        is_included_in_menu=group.is_included_in_menu,
        is_active=group.is_active
    )
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"Created group: {db_group.id} - {db_group.name_en}")
    return db_group


def update_group(db: Session, group_id: UUID, group_update: GroupUpdate) -> Optional[Group]:
    """Update an existing group."""
    db_group = get_group(db, group_id)
    
    if not db_group:
        return None
    
    update_data = group_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"Updated group: {db_group.id}")
    return db_group


def upsert_group(db: Session, group: GroupCreate) -> Group:
    """Create or update a group based on iiko_id."""
    existing = get_group_by_iiko_id(db, group.iiko_id)
    
    if existing:
        update_data = GroupUpdate(
            name_uz=group.name_uz,
            name_ru=group.name_ru,
            name_en=group.name_en,
            description_uz=group.description_uz,
            description_ru=group.description_ru,
            description_en=group.description_en,
            parent_group_id=group.parent_group_id,
            order=group.order,
            is_included_in_menu=group.is_included_in_menu,
            is_active=group.is_active
        )
        return update_group(db, existing.id, update_data)
    
    return create_group(db, group)


def delete_group(db: Session, group_id: UUID) -> bool:
    """Delete a group."""
    db_group = get_group(db, group_id)
    
    if not db_group:
        return False
    
    db.delete(db_group)
    db.commit()
    
    logger.info(f"Deleted group: {group_id}")
    return True
