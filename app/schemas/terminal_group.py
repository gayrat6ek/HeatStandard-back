from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class TerminalGroupBase(BaseModel):
    """Base terminal group schema."""
    name: str


class TerminalGroupCreate(TerminalGroupBase):
    """Schema for creating terminal group."""
    iiko_id: str
    organization_id: UUID


class TerminalGroupUpdate(BaseModel):
    """Schema for updating terminal group."""
    name: Optional[str] = None
    is_active: Optional[bool] = None


class TerminalGroupResponse(TerminalGroupBase):
    """Schema for terminal group response."""
    id: UUID
    iiko_id: str
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TerminalGroupList(BaseModel):
    """Schema for terminal group list response."""
    total: int
    items: list[TerminalGroupResponse]
