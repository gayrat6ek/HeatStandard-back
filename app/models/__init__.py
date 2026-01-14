"""Models package - Import all models in correct order for SQLAlchemy relationships."""

# Import base first
from app.database import Base

# Import models in dependency order
from app.models.user import User, UserRole, Language
from app.models.organization import Organization
from app.models.group import Group
from app.models.product import Product
from app.models.terminal_group import TerminalGroup
from app.models.section import Section
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Language",
    "Organization",
    "Group",
    "Product",
    "TerminalGroup",
    "Section",
    "Order",
    "OrderStatus",
    "OrderItem",
]

