from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class TerminalGroup(Base):
    """Terminal group model representing iiko terminal groups."""
    
    __tablename__ = "terminal_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="terminal_groups")
    sections = relationship("Section", back_populates="terminal_group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TerminalGroup(id={self.id}, name={self.name})>"
