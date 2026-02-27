from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Enum as SQLEnum, Integer, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"


# Sequence for order numbers starting from 10000
order_number_seq = Sequence('order_number_seq', start=10000)


class Order(Base):
    """Order model representing customer orders."""
    
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(Integer, order_number_seq, server_default=order_number_seq.next_value(), unique=True, nullable=False, index=True)
    iiko_order_id = Column(String, unique=True, nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Initially nullable for migration compatibility
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    delivery_address = Column(String, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.pending, nullable=False)
    notes = Column(String, nullable=True)
    telegram_message_id = Column(Integer, nullable=True)  # Message ID in admin group for editing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="orders")
    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"
