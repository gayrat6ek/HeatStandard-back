from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class SectionBase(BaseModel):
    """Base section schema."""
    name: str
    table_number: Optional[int] = None


class SectionCreate(SectionBase):
    """Schema for creating section."""
    iiko_id: str
    organization_id: UUID
    terminal_group_id: Optional[UUID] = None


class SectionUpdate(BaseModel):
    """Schema for updating section."""
    name: Optional[str] = None
    is_active: Optional[bool] = None


class SectionResponse(SectionBase):
    """Schema for section response."""
    id: UUID
    iiko_id: str
    organization_id: UUID
    terminal_group_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SectionList(BaseModel):
    """Schema for section list response."""
    total: int
    items: list[SectionResponse]
