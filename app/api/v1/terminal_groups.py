from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.terminal_group import TerminalGroupResponse, TerminalGroupList
from app.crud import terminal_group as crud_terminal_group
from app.crud import organization as crud_organization
from app.services.iiko_service import iiko_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=TerminalGroupList)
async def list_terminal_groups(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all terminal groups.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **organization_id**: Filter by organization
    - **is_active**: Filter by active status
    """
    terminal_groups = crud_terminal_group.get_terminal_groups(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        is_active=is_active
    )
    total = crud_terminal_group.get_terminal_groups_count(
        db=db,
        organization_id=organization_id,
        is_active=is_active
    )
    
    return TerminalGroupList(total=total, items=terminal_groups)


@router.get("/{terminal_group_id}", response_model=TerminalGroupResponse)
async def get_terminal_group(
    terminal_group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get terminal group by ID."""
    terminal_group = crud_terminal_group.get_terminal_group(db=db, terminal_group_id=terminal_group_id)
    
    if not terminal_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal group not found"
        )
    
    return terminal_group


@router.post("/sync")
async def sync_terminal_groups(
    organization_ids: Optional[list[str]] = Query(None, description="Organization IDs to sync"),
    db: Session = Depends(get_db)
):
    """
    Sync terminal groups from iiko API to database.
    
    Fetches terminal groups from iiko and creates/updates them in the database.
    If no organization_ids provided, syncs all organizations from database.
    """
    try:
        # If no organization IDs provided, get all from database
        if not organization_ids:
            db_organizations = crud_organization.get_organizations(db=db, limit=1000)
            organization_ids = [org.iiko_id for org in db_organizations]
        
        if not organization_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No organizations found. Please sync organizations first."
            )
        
        synced_count = 0
        errors = []
        
        # Fetch terminal groups from iiko
        terminal_groups_response = await iiko_service.get_terminal_groups(organization_ids)
        
        # Iterate over organizations and their terminal groups
        for org_data in terminal_groups_response:
            org_iiko_id = org_data.get("organizationId")
            items = org_data.get("items", [])
            
            # Get organization from database
            org = crud_organization.get_organization_by_iiko_id(db=db, iiko_id=org_iiko_id)
            
            if not org:
                logger.warning(f"Organization not found: {org_iiko_id}")
                continue
            
            for iiko_tg in items:
                try:
                    terminal_group_data = {
                        "iiko_id": iiko_tg.get("id"),
                        "name": iiko_tg.get("name"),
                        "organization_id": org.id,
                    }
                    
                    crud_terminal_group.upsert_terminal_group(db=db, terminal_group_data=terminal_group_data)
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing terminal group {iiko_tg.get('id')}: {e}")
                    errors.append(str(e))
        
        return {
            "message": f"Successfully synced {synced_count} terminal groups",
            "synced_count": synced_count,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync terminal groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync terminal groups: {str(e)}"
        )
