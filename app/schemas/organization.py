from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str
    country: Optional[str] = None
    restaurant_address: Optional[str] = None
    use_uae_addressing: bool = False
    timezone: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization."""
    iiko_id: str


class OrganizationUpdate(BaseModel):
    """Schema for updating organization."""
    name: Optional[str] = None
    country: Optional[str] = None
    restaurant_address: Optional[str] = None
    use_uae_addressing: Optional[bool] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: UUID
    iiko_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationList(BaseModel):
    """Schema for organization list response."""
    total: int
    items: list[OrganizationResponse]
