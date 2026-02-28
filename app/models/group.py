from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, column_property
from datetime import datetime
import uuid

from app.database import Base
from app.models.product import Product


class Group(Base):
    """Group model for iiko menu groups hierarchy.
    
    Groups can have parent-child relationships, forming a tree structure.
    Products are linked to groups (leaf or any level).
    """
    
    __tablename__ = "groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iiko_id = Column(String, unique=True, nullable=False, index=True)
    
    # Multi-language names
    name_uz = Column(String, nullable=False)  # Uzbek
    name_ru = Column(String, nullable=False)  # Russian
    name_en = Column(String, nullable=False)  # English
    
    # Multi-language descriptions
    description_uz = Column(String, nullable=True)
    description_ru = Column(String, nullable=True)
    description_en = Column(String, nullable=True)
    
    # Hierarchy - self-referential foreign key
    parent_group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    
    order = Column(Integer, default=0)  # Display order
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_included_in_menu = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="groups")
    parent = relationship("Group", remote_side=[id], back_populates="children")
    children = relationship("Group", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="group", cascade="all, delete-orphan")
    
    # Active products count property
    active_products_count = column_property(
        select(func.count(Product.id))
        .where(
            and_(
                Product.group_id == id,
                Product.is_active == True
            )
        )
        .correlate_except(Product)
        .scalar_subquery()
    )
    
    def __repr__(self):
        return f"<Group(id={self.id}, name_en={self.name_en}, parent_id={self.parent_group_id})>"
