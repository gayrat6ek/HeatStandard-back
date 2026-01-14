"""sdf

Revision ID: e06f09bd637d
Revises: 48147a981440
Create Date: 2026-01-14 15:52:17.792761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e06f09bd637d'
down_revision = '48147a981440'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First drop existing orders and order_items tables (user confirmed this is OK)
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP SEQUENCE IF EXISTS order_number_seq CASCADE")
    
    # Drop and recreate the enum type with correct values
    op.execute("DROP TYPE IF EXISTS orderstatus CASCADE")
    op.execute("""
        CREATE TYPE orderstatus AS ENUM (
            'pending', 'sent_to_iiko', 'confirmed', 'in_progress', 
            'completed', 'cancelled', 'failed', 'declined'
        )
    """)
    
    # Create sequence for order numbers starting from 10000
    op.execute("CREATE SEQUENCE order_number_seq START WITH 10000")
    
    # Recreate orders table
    op.execute("""
        CREATE TABLE orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_number INTEGER NOT NULL DEFAULT nextval('order_number_seq') UNIQUE,
            iiko_order_id VARCHAR UNIQUE,
            organization_id UUID NOT NULL REFERENCES organizations(id),
            customer_name VARCHAR NOT NULL,
            customer_phone VARCHAR NOT NULL,
            customer_email VARCHAR,
            delivery_address VARCHAR,
            total_amount NUMERIC(10, 2) NOT NULL,
            status orderstatus NOT NULL DEFAULT 'pending',
            notes VARCHAR,
            telegram_message_id INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX ix_orders_order_number ON orders(order_number)")
    op.execute("CREATE INDEX ix_orders_iiko_order_id ON orders(iiko_order_id)")
    
    # Recreate order_items table
    op.execute("""
        CREATE TABLE order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id UUID NOT NULL,
            product_name VARCHAR NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            total NUMERIC(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP SEQUENCE IF EXISTS order_number_seq")
