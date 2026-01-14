from sqlalchemy import Column, String, Numeric, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Product(Base):
    """Product model representing iiko menu items/products."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id = Column(String, unique=True, nullable=False, index=True)
    
    # Multi-language names
    name_uz = Column(String, nullable=False)  # Uzbek
    name_ru = Column(String, nullable=False)  # Russian
    name_en = Column(String, nullable=False)  # English
    
    # Multi-language descriptions
    description_uz = Column(Text, nullable=True)  # Uzbek
    description_ru = Column(Text, nullable=True)  # Russian
    description_en = Column(Text, nullable=True)  # English
    
    price = Column(Numeric(10, 2), nullable=True)
    images = Column(JSON, default=list)  # List of image URLs
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="products")
    group = relationship("Group", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name_en={self.name_en})>"

