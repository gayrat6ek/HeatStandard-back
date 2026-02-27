from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderList, OrderUpdate
from app.models.order import OrderStatus
from app.models.user import User
from app.crud import order as crud_order
from app.crud import organization as crud_organization
from app.services.iiko_service import iiko_service
from app.api.dependencies import get_current_active_user


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=OrderList)
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    db: Session = Depends(get_db)
):
    """
    Get list of all orders.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **organization_id**: Filter by organization
    - **user_id**: Filter by user ID
    - **status**: Filter by order status
    """
    orders = crud_order.get_orders(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        user_id=user_id,
        status=status_filter
    )
    total = crud_order.get_orders_count(
        db=db,
        organization_id=organization_id,
        user_id=user_id,
        status=status_filter
    )
    
    return OrderList(total=total, items=orders)


@router.get("/me", response_model=OrderList)
async def list_my_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of orders for the current authenticated user.
    """
    orders = crud_order.get_user_orders(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status_filter
    )
    total = crud_order.get_user_orders_count(
        db=db,
        user_id=current_user.id,
        status=status_filter
    )
    
    return OrderList(total=total, items=orders)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Session = Depends(get_db)
):
    """Get order by ID."""
    order = crud_order.get_order(db=db, order_id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_update: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update order (PUT - full update).
    
    Allows updating order status and other details.
    If status is set to 'confirmed', the order will be sent to iiko.
    """
    updated_order = crud_order.update_order(
        db=db,
        order_id=order_id,
        order_update=order_update
    )
    
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Send to iiko when order is confirmed
    if order_update.status == OrderStatus.confirmed:
        await _send_order_to_iiko(updated_order, db)
    
    return updated_order


@router.patch("/{order_id}", response_model=OrderResponse)
async def patch_order(
    order_id: UUID,
    order_update: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Partially update order (PATCH).
    
    Allows updating order status, telegram_message_id, notes, etc.
    If status is set to 'confirmed', the order will be sent to iiko.
    """
    updated_order = crud_order.update_order(
        db=db,
        order_id=order_id,
        order_update=order_update
    )
    
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Send to iiko when order is confirmed
    if order_update.status == OrderStatus.confirmed:
        await _send_order_to_iiko(updated_order, db)
    
    return updated_order


async def _send_order_to_iiko(order, db: Session):
    """
    Send a confirmed order to iiko and update with the returned iiko order ID.
    On failure, logs the error but does not revert the confirmation.
    """
    try:
        iiko_order_id = await iiko_service.send_order_to_iiko(order, db)
        if iiko_order_id:
            crud_order.update_order_iiko_id(
                db=db,
                order_id=order.id,
                iiko_order_id=iiko_order_id
            )
            logger.info(f"Order {order.id} sent to iiko successfully, iiko_id={iiko_order_id}")
        else:
            logger.warning(f"Order {order.id} confirmed but iiko did not return an order ID")
    except Exception as e:
        logger.error(f"Failed to send order {order.id} to iiko: {e}")


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order.
    
    Orders are created with 'pending' status.
    Uses provided user_id or falls back to current authenticated user.
    """
    try:
        # Verify organization exists
        organization = crud_organization.get_organization(db=db, organization_id=order_data.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Use provided user_id or fallback to current_user
        user_id = order_data.user_id or current_user.id
        
        # Create order in database
        db_order = crud_order.create_order(db=db, order=order_data, user_id=user_id)
        
        logger.info(f"Order {db_order.id} created successfully for user {user_id}")
        
        return db_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )
