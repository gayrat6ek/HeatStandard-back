from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class OrderItem(Base):
    """Order item model representing individual items in an order."""
    
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)  # Nullable in case product is deleted
    product_name = Column(String, nullable=False)  # Store name in case product is deleted
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Price at time of order
    total = Column(Numeric(10, 2), nullable=False)  # quantity * price
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_name={self.product_name}, quantity={self.quantity})>"
