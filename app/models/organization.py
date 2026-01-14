from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Organization(Base):
    """Organization model representing iiko organizations."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    restaurant_address = Column(String, nullable=True)
    use_uae_addressing = Column(Boolean, default=False)
    timezone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    groups = relationship("Group", back_populates="organization", cascade="all, delete-orphan", lazy="dynamic")
    products = relationship("Product", back_populates="organization", cascade="all, delete-orphan", lazy="dynamic")
    sections = relationship("Section", back_populates="organization", cascade="all, delete-orphan", lazy="dynamic")
    terminal_groups = relationship("TerminalGroup", back_populates="organization", cascade="all, delete-orphan", lazy="dynamic")
    orders = relationship("Order", back_populates="organization", cascade="all, delete-orphan", lazy="dynamic")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"
