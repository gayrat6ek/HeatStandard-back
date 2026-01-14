from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.section import SectionResponse, SectionList
from app.crud import section as crud_section
from app.crud import organization as crud_organization
from app.services.iiko_service import iiko_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=SectionList)
async def list_sections(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all restaurant sections.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **organization_id**: Filter by organization
    - **is_active**: Filter by active status
    """
    sections = crud_section.get_sections(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        is_active=is_active
    )
    total = crud_section.get_sections_count(
        db=db,
        organization_id=organization_id,
        is_active=is_active
    )
    
    return SectionList(total=total, items=sections)


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: UUID,
    db: Session = Depends(get_db)
):
    """Get section by ID."""
    section = crud_section.get_section(db=db, section_id=section_id)
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    return section


@router.post("/sync")
async def sync_sections(
    organization_ids: Optional[list[str]] = Query(None, description="Organization IDs to sync"),
    db: Session = Depends(get_db)
):
    """
    Sync restaurant sections (tables) from iiko API to database.
    
    Fetches available restaurant sections from iiko terminal groups
    and creates/updates them in the database.
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
        
        # First, get terminal groups
        terminal_groups_response = await iiko_service.get_terminal_groups(organization_ids)
        
        # Collect all terminal group IDs and create a mapping
        terminal_group_map = {}  # iiko_id -> (org, db_terminal_group)
        all_terminal_group_ids = []
        
        # Iterate over organizations and their terminal groups
        for org_data in terminal_groups_response:
            org_iiko_id = org_data.get("organizationId")
            items = org_data.get("items", [])
            
            # Get organization from database
            org = crud_organization.get_organization_by_iiko_id(db=db, iiko_id=org_iiko_id)
            
            if not org:
                logger.warning(f"Organization not found: {org_iiko_id}")
                continue
            
            for terminal_group in items:
                try:
                    terminal_group_iiko_id = terminal_group.get("id")
                    terminal_group_name = terminal_group.get("name")
                    
                    # Get or create terminal group in database
                    from app.crud import terminal_group as crud_terminal_group
                    db_terminal_group = crud_terminal_group.get_terminal_group_by_iiko_id(
                        db=db,
                        iiko_id=terminal_group_iiko_id
                    )
                    
                    if not db_terminal_group:
                        # Create terminal group if it doesn't exist
                        from app.schemas.terminal_group import TerminalGroupCreate
                        tg_create = TerminalGroupCreate(
                            iiko_id=terminal_group_iiko_id,
                            name=terminal_group_name,
                            organization_id=org.id
                        )
                        db_terminal_group = crud_terminal_group.create_terminal_group(db=db, terminal_group=tg_create)
                    
                    terminal_group_map[terminal_group_iiko_id] = (org, db_terminal_group)
                    all_terminal_group_ids.append(terminal_group_iiko_id)
                    
                except Exception as e:
                    logger.error(f"Error processing terminal group: {e}")
                    errors.append(str(e))
        
        # Now fetch all restaurant sections in one call
        if all_terminal_group_ids:
            try:
                sections = await iiko_service.get_available_restaurant_sections(all_terminal_group_ids)
                
                # Process each section
                for iiko_section in sections:
                    try:
                        terminal_group_id = iiko_section.get("terminalGroupId")
                        
                        if terminal_group_id not in terminal_group_map:
                            logger.warning(f"Terminal group not found in map: {terminal_group_id}")
                            continue
                        
                        org, db_terminal_group = terminal_group_map[terminal_group_id]
                        
                        # Extract table information
                        tables = iiko_section.get("tables", [])
                        
                        # If there are specific tables, create a section for each
                        if tables:
                            for table in tables:
                                # Skip deleted tables
                                if table.get("isDeleted"):
                                    continue
                                    
                                section_data = {
                                    "iiko_id": table.get("id"),
                                    "name": table.get("name") or iiko_section.get("name"),
                                    "table_number": table.get("number"),
                                    "terminal_group_id": db_terminal_group.id,
                                    "organization_id": org.id,
                                }
                                
                                crud_section.upsert_section(db=db, section_data=section_data)
                                synced_count += 1
                        else:
                            # No specific tables, create section for the whole area
                            section_data = {
                                "iiko_id": iiko_section.get("id"),
                                "name": iiko_section.get("name"),
                                "table_number": None,
                                "terminal_group_id": db_terminal_group.id,
                                "organization_id": org.id,
                            }
                            
                            crud_section.upsert_section(db=db, section_data=section_data)
                            synced_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error syncing section {iiko_section.get('id')}: {e}")
                        errors.append(str(e))
                        
            except Exception as e:
                logger.error(f"Error fetching sections: {e}")
                errors.append(str(e))
        
        return {
            "message": f"Successfully synced {synced_count} sections",
            "synced_count": synced_count,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync sections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync sections: {str(e)}"
        )
