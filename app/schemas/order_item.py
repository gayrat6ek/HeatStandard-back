from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_name: str
    quantity: int
    price: Decimal
    total: Decimal


class OrderItemCreate(OrderItemBase):
    """Schema for creating order item."""
    product_id: UUID


class OrderItemResponse(OrderItemBase):
    """Schema for order item response."""
    id: UUID
    product_id: Optional[UUID]
    order_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
