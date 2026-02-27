from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.models.order import OrderStatus


class OrderItem(BaseModel):
    """Schema for order item."""
    product_id: UUID
    product_name: str
    quantity: int = Field(gt=0)
    price: Decimal
    total: Decimal


class OrderBase(BaseModel):
    """Base order schema."""
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Schema for creating order."""
    organization_id: UUID
    user_id: Optional[UUID] = None
    items: list[OrderItem]


class OrderUpdate(BaseModel):
    """Schema for updating order."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    telegram_message_id: Optional[int] = None


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: UUID
    order_number: int
    iiko_order_id: Optional[str] = None
    organization_id: UUID
    items: list["OrderItemResponse"]  # Forward reference
    total_amount: Decimal
    status: OrderStatus
    telegram_message_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Import after OrderResponse to avoid circular import
from app.schemas.order_item import OrderItemResponse
OrderResponse.model_rebuild()


class OrderList(BaseModel):
    """Schema for order list response."""
    total: int
    items: list[OrderResponse]
