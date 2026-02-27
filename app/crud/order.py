from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
import logging

from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.utils.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def get_order(db: Session, order_id: UUID) -> Optional[Order]:
    """Get order by ID."""
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_iiko_id(db: Session, iiko_order_id: str) -> Optional[Order]:
    """Get order by iiko order ID."""
    return db.query(Order).filter(Order.iiko_order_id == iiko_order_id).first()


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = None,
    status: Optional[OrderStatus] = None,
    user_id: Optional[UUID] = None
) -> List[Order]:
    """Get list of orders with filters and pagination."""
    query = db.query(Order)
    
    if organization_id:
        query = query.filter(Order.organization_id == organization_id)
    
    if status:
        query = query.filter(Order.status == status)
        
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_orders_count(
    db: Session,
    organization_id: Optional[UUID] = None,
    status: Optional[OrderStatus] = None,
    user_id: Optional[UUID] = None
) -> int:
    """Get total count of orders."""
    query = db.query(Order)
    
    if organization_id:
        query = query.filter(Order.organization_id == organization_id)
    
    if status:
        query = query.filter(Order.status == status)
        
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    return query.count()


def create_order(db: Session, order: OrderCreate, user_id: Optional[UUID] = None) -> Order:
    """Create new order with order items."""
    try:
        # Calculate total amount
        total_amount = sum(Decimal(str(item.total)) for item in order.items)
        
        # Create order
        db_order = Order(
            organization_id=order.organization_id,
            user_id=user_id,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_email=order.customer_email,
            delivery_address=order.delivery_address,
            total_amount=total_amount,
            notes=order.notes,
            status=OrderStatus.pending
        )
        
        db.add(db_order)
        db.flush()  # Flush to get the order ID
        
        # Create order items
        from app.models.order_item import OrderItem
        for item in order.items:
            db_order_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                total=item.total
            )
            db.add(db_order_item)
        
        db.commit()
        db.refresh(db_order)
        logger.info(f"Created order: {db_order.id} for user: {user_id} with {len(order.items)} items")
        return db_order
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create order: {e}")
        raise DatabaseError(f"Failed to create order: {str(e)}")


def get_user_orders(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None
) -> List[Order]:
    """Get list of orders for a specific user."""
    query = db.query(Order).filter(Order.user_id == user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_user_orders_count(
    db: Session,
    user_id: UUID,
    status: Optional[OrderStatus] = None
) -> int:
    """Get total count of orders for a specific user."""
    query = db.query(Order).filter(Order.user_id == user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.count()


def update_order(
    db: Session,
    order_id: UUID,
    order_update: OrderUpdate
) -> Optional[Order]:
    """Update order."""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    logger.info(f"Updated order: {db_order.id}")
    return db_order


def update_order_iiko_id(db: Session, order_id: UUID, iiko_order_id: str) -> Optional[Order]:
    """Update order with iiko order ID after successful creation."""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    db_order.iiko_order_id = iiko_order_id
    db_order.status = OrderStatus.confirmed
    
    db.commit()
    db.refresh(db_order)
    logger.info(f"Updated order {order_id} with iiko_order_id: {iiko_order_id}")
    return db_order


def delete_order(db: Session, order_id: UUID) -> bool:
    """Delete order."""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return False
    
    db.delete(db_order)
    db.commit()
    logger.info(f"Deleted order: {db_order.id}")
    return True
