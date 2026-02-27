from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.organization import OrganizationResponse, OrganizationList, OrganizationUpdate
from app.crud import organization as crud_organization
from app.services.iiko_service import iiko_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=OrganizationList)
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all organizations.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Filter by active status
    """
    organizations = crud_organization.get_organizations(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    total = crud_organization.get_organizations_count(db=db, is_active=is_active)
    
    return OrganizationList(total=total, items=organizations)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get organization by ID."""
    organization = crud_organization.get_organization(db=db, organization_id=organization_id)
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    organization_update: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update organization.
    
    Allows updating organization details and active status.
    """
    updated_org = crud_organization.update_organization(
        db=db,
        organization_id=organization_id,
        organization_update=organization_update
    )
    
    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return updated_org


@router.post("/sync")
async def sync_organizations(
    db: Session = Depends(get_db)
):
    """
    Sync organizations from iiko API to database.
    
    Fetches all organizations from iiko and creates/updates them in the database.
    """
    try:
        # Fetch organizations from iiko
        iiko_organizations = await iiko_service.get_organizations()
        
        synced_count = 0
        errors = []
        
        for iiko_org in iiko_organizations:
            try:
                org_data = {
                    "iiko_id": iiko_org.get("id"),
                    "name": iiko_org.get("name"),
                    "country": iiko_org.get("country"),
                    "restaurant_address": iiko_org.get("restaurantAddress"),
                    "use_uae_addressing": iiko_org.get("useUaeAddressingSystem", False),
                    "timezone": iiko_org.get("timezone"),
                }
                
                crud_organization.upsert_organization(db=db, organization_data=org_data)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing organization {iiko_org.get('id')}: {e}")
                errors.append(str(e))
        
        return {
            "message": f"Successfully synced {synced_count} organizations",
            "synced_count": synced_count,
            "total_from_iiko": len(iiko_organizations),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Failed to sync organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync organizations: {str(e)}"
        )
