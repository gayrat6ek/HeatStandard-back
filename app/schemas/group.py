from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class GroupBase(BaseModel):
    """Base Group schema with common fields."""
    name_uz: str
    name_ru: str
    name_en: str
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    order: int = 0
    is_included_in_menu: bool = True
    is_active: bool = True


class GroupCreate(GroupBase):
    """Schema for creating a new group."""
    iiko_id: str
    parent_group_id: Optional[UUID] = None
    organization_id: UUID


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    parent_group_id: Optional[UUID] = None
    order: Optional[int] = None
    is_included_in_menu: Optional[bool] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """Schema for group response."""
    id: UUID
    iiko_id: str
    parent_group_id: Optional[UUID] = None
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GroupWithChildren(GroupResponse):
    """Schema for group with nested children."""
    children: List["GroupWithChildren"] = []
    
    class Config:
        from_attributes = True


class GroupList(BaseModel):
    """Schema for paginated group list."""
    total: int
    items: List[GroupResponse]


# For forward reference resolution
GroupWithChildren.model_rebuild()
