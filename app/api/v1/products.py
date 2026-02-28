from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.product import ProductResponse, ProductList, ProductUpdate
from app.crud import product as crud_product
from app.crud import organization as crud_organization
from app.services.iiko_service import iiko_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ProductList)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    group_id: Optional[UUID] = Query(None, description="Filter by group ID"),
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    Get list of all products.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **organization_id**: Filter by organization
    - **group_id**: Filter by group
    - **is_active**: Filter by active status
    - **search**: Search term for product name
    """
    products = crud_product.get_products(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        group_id=group_id,
        is_active=is_active,
        search=search
    )
    total = crud_product.get_products_count(
        db=db,
        organization_id=organization_id,
        group_id=group_id,
        is_active=is_active,
        search=search
    )
    return ProductList(total=total, items=products)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get product by ID."""
    product = crud_product.get_product(db=db, product_id=product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a product.
    
    Allows updating multi-language names, descriptions, price, images, and subcategory.
    """
    from app.schemas.product import ProductUpdate
    
    product = crud_product.update_product(
        db=db,
        product_id=product_id,
        product_update=product_update
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a product."""
    if not crud_product.delete_product(db=db, product_id=product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


@router.post("/sync")
async def sync_products(
    organization_ids: Optional[list[str]] = Query(None, description="Organization IDs to sync (max 5)"),
    db: Session = Depends(get_db)
):
    """
    Sync groups and products from iiko API to database.
    
    Fetches nomenclature (groups and products) from iiko and creates/updates them in the database.
    If no organization_ids provided, syncs all organizations from database.
    """
    from app.crud import group as crud_group
    from app.schemas.group import GroupCreate
    
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
        
        synced_groups = 0
        synced_products = 0
        errors = []
        
        try:
            # Fetch groups and products from Resto API once
            resto_groups = await iiko_service.get_resto_groups()
            resto_products = await iiko_service.get_resto_products()
        except Exception as e:
            logger.error(f"Failed to fetch data from Resto API: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch data from Resto API: {str(e)}"
            )
            
        # Process each organization individually
        for org_iiko_id in organization_ids:
            try:
                # Get organization from database
                org = crud_organization.get_organization_by_iiko_id(db=db, iiko_id=org_iiko_id)
                
                if not org:
                    logger.warning(f"Organization not found in database: {org_iiko_id}")
                    continue
                
                # Build iiko_id to db_id mapping for groups
                group_id_map = {}
                
                # First pass: Sync groups (need to handle parent references)
                # Sort groups: root groups first (parent is null)
                root_groups = [g for g in resto_groups if g.get("parent") is None]
                child_groups = [g for g in resto_groups if g.get("parent") is not None]
                
                # Create root groups first
                for iiko_group in root_groups:
                    try:
                        if iiko_group.get("deleted"):
                            continue
                        
                        name = iiko_group.get("name") or "Unnamed Group"
                        
                        group_data = GroupCreate(
                            iiko_id=iiko_group.get("id"),
                            name_uz=name,
                            name_ru=name,
                            name_en=name,
                            description_uz=iiko_group.get("description"),
                            description_ru=iiko_group.get("description"),
                            description_en=iiko_group.get("description"),
                            parent_group_id=None,
                            organization_id=org.id,
                            order=0,
                            is_included_in_menu=True,
                            is_active=True
                        )
                        
                        db_group = crud_group.upsert_group(db=db, group=group_data)
                        group_id_map[iiko_group.get("id")] = db_group.id
                        synced_groups += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing root group {iiko_group.get('id')}: {e}")
                        errors.append(str(e))
                
                # Create child groups (may need multiple passes for deep hierarchies)
                remaining = child_groups.copy()
                max_iterations = 10
                iteration = 0
                
                while remaining and iteration < max_iterations:
                    iteration += 1
                    still_remaining = []
                    
                    for iiko_group in remaining:
                        try:
                            if iiko_group.get("deleted"):
                                continue
                            
                            parent_iiko_id = iiko_group.get("parent")
                            
                            # Check if parent is already mapped
                            if parent_iiko_id in group_id_map:
                                name = iiko_group.get("name") or "Unnamed Group"
                                
                                group_data = GroupCreate(
                                    iiko_id=iiko_group.get("id"),
                                    name_uz=name,
                                    name_ru=name,
                                    name_en=name,
                                    description_uz=iiko_group.get("description"),
                                    description_ru=iiko_group.get("description"),
                                    description_en=iiko_group.get("description"),
                                    parent_group_id=group_id_map[parent_iiko_id],
                                    organization_id=org.id,
                                    order=0,
                                    is_included_in_menu=True,
                                    is_active=True
                                )
                                
                                db_group = crud_group.upsert_group(db=db, group=group_data)
                                group_id_map[iiko_group.get("id")] = db_group.id
                                synced_groups += 1
                            else:
                                # Parent not yet created, defer
                                still_remaining.append(iiko_group)
                                
                        except Exception as e:
                            logger.error(f"Error syncing child group {iiko_group.get('id')}: {e}")
                            errors.append(str(e))
                    
                    remaining = still_remaining
                
                logger.info(f"Synced groups for organization {org.name}")
                
                # Second pass: Sync products and link to groups
                for iiko_product in resto_products:
                    try:
                        if iiko_product.get("deleted"):
                            continue
                        
                        # Product from Resto API doesn't have imageLinks
                        images = []
                        name = iiko_product.get("name") or "Unnamed Product"
                        description = iiko_product.get("description") or ""
                        
                        # Price is defaultSalePrice
                        price = iiko_product.get("defaultSalePrice", 0) or 0
                        
                        # Get group_id from mapping
                        parent_group_iiko_id = iiko_product.get("parent")
                        group_id = group_id_map.get(parent_group_iiko_id) if parent_group_iiko_id else None
                        
                        product_data = {
                            "iiko_id": iiko_product.get("id"),
                            "name_uz": name,
                            "name_ru": name,
                            "name_en": name,
                            "description_uz": description,
                            "description_ru": description,
                            "description_en": description,
                            "price": price,
                            "images": images,
                            "organization_id": org.id,
                            "group_id": group_id,
                        }
                        
                        crud_product.upsert_product(db=db, product_data=product_data)
                        synced_products += 1
                        
                    except Exception as e:
                        logger.error(f"Error syncing product {iiko_product.get('id')}: {e}")
                        errors.append(str(e))
                
                logger.info(f"Synced products for organization {org.name}")
                
            except Exception as e:
                logger.error(f"Error syncing organization {org_iiko_id}: {e}")
                errors.append(f"Organization {org_iiko_id}: {str(e)}")
        
        return {
            "message": f"Successfully synced {synced_groups} groups and {synced_products} products",
            "synced_groups": synced_groups,
            "synced_products": synced_products,
            "organizations_processed": len(organization_ids),
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync: {str(e)}"
        )

