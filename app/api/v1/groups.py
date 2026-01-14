from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.group import GroupCreate, GroupResponse, GroupList, GroupUpdate
from app.crud import group as crud_group


router = APIRouter()


@router.get("", response_model=GroupList)
async def list_groups(
    skip: int = 0,
    limit: int = 100,
    parent_id: Optional[str] = Query(None, description="Parent group ID. Use 'null' for root groups."),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    db: Session = Depends(get_db)
):
    """
    Get list of groups.
    
    - **parent_id**: Filter by parent group. Use 'null' string to get root groups.
    - **organization_id**: Filter by organization
    """
    # Handle 'null' string for root groups
    root_only = parent_id == "null"
    parent_group_id = None
    
    if parent_id and parent_id != "null":
        try:
            parent_group_id = UUID(parent_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parent_id format"
            )
    
    groups = crud_group.get_groups(
        db=db,
        skip=skip,
        limit=limit,
        parent_group_id=parent_group_id,
        organization_id=organization_id,
        root_only=root_only
    )
    
    total = crud_group.get_groups_count(
        db=db,
        parent_group_id=parent_group_id,
        organization_id=organization_id,
        root_only=root_only
    )
    
    return GroupList(total=total, items=groups)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single group by ID."""
    group = crud_group.get_group(db=db, group_id=group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return group


@router.get("/{group_id}/children", response_model=GroupList)
async def get_group_children(
    group_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get direct children of a group."""
    # Verify parent exists
    parent = crud_group.get_group(db=db, group_id=group_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent group not found"
        )
    
    groups = crud_group.get_groups(
        db=db,
        skip=skip,
        limit=limit,
        parent_group_id=group_id
    )
    
    total = crud_group.get_groups_count(
        db=db,
        parent_group_id=group_id
    )
    
    return GroupList(total=total, items=groups)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db)
):
    """Create a new group."""
    # Check if parent exists (if specified)
    if group.parent_group_id:
        parent = crud_group.get_group(db=db, group_id=group.parent_group_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent group not found"
            )
    
    return crud_group.create_group(db=db, group=group)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    group_update: GroupUpdate,
    db: Session = Depends(get_db)
):
    """Update a group."""
    updated_group = crud_group.update_group(
        db=db,
        group_id=group_id,
        group_update=group_update
    )
    
    if not updated_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return updated_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a group."""
    success = crud_group.delete_group(db=db, group_id=group_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return None
