from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import logging

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_product(db: Session, product_id: UUID) -> Optional[Product]:
    """Get product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_iiko_id(db: Session, iiko_id: str) -> Optional[Product]:
    """Get product by iiko ID."""
    return db.query(Product).filter(Product.iiko_id == iiko_id).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = None,
    group_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Product]:
    """Get list of products with filters, search, and pagination."""
    query = db.query(Product)
    
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    
    if group_id:
        query = query.filter(Product.group_id == group_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
        
    if search:
        search_filter = or_(
            Product.name_ru.ilike(f"%{search}%"),
            Product.name_en.ilike(f"%{search}%"),
            Product.name_uz.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Default sorting by name_ru
    query = query.order_by(Product.name_ru.asc())
    
    return query.offset(skip).limit(limit).all()


def get_products_count(
    db: Session,
    organization_id: Optional[UUID] = None,
    group_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> int:
    """Get total count of products."""
    query = db.query(Product)
    
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    
    if group_id:
        query = query.filter(Product.group_id == group_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    if search:
        search_filter = or_(
            Product.name_ru.ilike(f"%{search}%"),
            Product.name_en.ilike(f"%{search}%"),
            Product.name_uz.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.count()


def create_product(db: Session, product: ProductCreate) -> Product:
    """Create new product."""
    try:
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Created product: {db_product.name_ru}")
        return db_product
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create product: {e}")
        raise DatabaseError(f"Product with iiko_id already exists")


def update_product(
    db: Session,
    product_id: UUID,
    product_update: ProductUpdate
) -> Optional[Product]:
    """Update product."""
    db_product = get_product(db, product_id)
    
    if not db_product:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    logger.info(f"Updated product: {db_product.name_ru}")
    return db_product


def upsert_product(db: Session, product_data: dict) -> Product:
    """Create or update product based on iiko_id."""
    existing = get_product_by_iiko_id(db, product_data["iiko_id"])
    
    if existing:
        # Update existing
        for key, value in product_data.items():
            if key != "id" and hasattr(existing, key):
                # Don't overwrite existing images with an empty list
                if key == "images" and not value and getattr(existing, "images"):
                    continue
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        product_create = ProductCreate(**product_data)
        return create_product(db, product_create)


def delete_product(db: Session, product_id: UUID) -> bool:
    """Delete product."""
    db_product = get_product(db, product_id)
    
    if not db_product:
        return False
    
    db.delete(db_product)
    db.commit()
    logger.info(f"Deleted product: {db_product.name_ru}")
    return True


def mark_missing_products_inactive(db: Session, organization_id: UUID, active_iiko_ids: List[str]) -> int:
    """Mark products as inactive if they are not in the provided list of active iiko_ids."""
    from sqlalchemy import update
    
    # Update products that belong to the organization and are NOT in the active_iiko_ids list
    stmt = (
        update(Product)
        .where(Product.organization_id == organization_id)
        .where(Product.iiko_id.not_in(active_iiko_ids))
        .where(Product.is_active == True)
        .values(is_active=False)
    )
    
    result = db.execute(stmt)
    db.commit()
    
    deactivated_count = result.rowcount
    if deactivated_count > 0:
        logger.info(f"Deactivated {deactivated_count} products for organization {organization_id}")
        
    return deactivated_count
