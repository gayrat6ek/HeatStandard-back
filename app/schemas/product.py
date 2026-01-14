from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema."""
    name_uz: str
    name_ru: str
    name_en: str
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price: Optional[Decimal] = None
    images: list[str] = []


class ProductCreate(ProductBase):
    """Schema for creating product."""
    iiko_id: str
    group_id: Optional[UUID] = None
    organization_id: UUID


class ProductUpdate(BaseModel):
    """Schema for updating product."""
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price: Optional[Decimal] = None
    images: Optional[list[str]] = None
    group_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: UUID
    iiko_id: str
    group_id: Optional[UUID]
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """Schema for product list response."""
    total: int
    items: list[ProductResponse]
