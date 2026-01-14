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
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    db: Session = Depends(get_db)
):
    """
    Get list of all orders.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **organization_id**: Filter by organization
    - **status**: Filter by order status
    """
    orders = crud_order.get_orders(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        status=status_filter
    )
    total = crud_order.get_orders_count(
        db=db,
        organization_id=organization_id,
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
    
    return updated_order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order and send it to iiko.
    
    Requires an active user account. Inactive users cannot place orders.
    
    This endpoint:
    1. Creates the order in the local database
    2. Sends the order to iiko API
    3. Updates the order with iiko order ID
    """
    try:
        # Verify organization exists
        organization = crud_organization.get_organization(db=db, organization_id=order.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Create order in database
        db_order = crud_order.create_order(db=db, order=order)
        
        logger.info(f"Order {db_order.id} created successfully in database")
        
        # TODO: iiko integration disabled for now
        # When ready to integrate with iiko, uncomment the code below
        # try:
        #     iiko_response = await iiko_service.create_delivery_order(iiko_order_data)
        #     iiko_order_id = iiko_response.get("orderInfo", {}).get("id")
        #     if iiko_order_id:
        #         db_order = crud_order.update_order_iiko_id(db=db, order_id=db_order.id, iiko_order_id=iiko_order_id)
        # except Exception as e:
        #     logger.error(f"Failed to send order to iiko: {e}")
        
        return db_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )
