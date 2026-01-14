from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Section(Base):
    """Restaurant section model representing iiko restaurant sections/tables."""
    
    __tablename__ = "sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    table_number = Column(Integer, nullable=True)  # Table number if applicable
    terminal_group_id = Column(UUID(as_uuid=True), ForeignKey("terminal_groups.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="sections")
    terminal_group = relationship("TerminalGroup", back_populates="sections")
    
    def __repr__(self):
        return f"<Section(id={self.id}, name={self.name}, table_number={self.table_number})>"
