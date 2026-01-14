"""Replace categories and subcategories with groups

Revision ID: 48147a981440
Revises: 6d0c5ea7f211
Create Date: 2026-01-13 13:25:33.916097

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '48147a981440'
down_revision = '6d0c5ea7f211'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create groups table first
    op.create_table('groups',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('iiko_id', sa.String(), nullable=False),
        sa.Column('name_uz', sa.String(), nullable=False),
        sa.Column('name_ru', sa.String(), nullable=False),
        sa.Column('name_en', sa.String(), nullable=False),
        sa.Column('description_uz', sa.String(), nullable=True),
        sa.Column('description_ru', sa.String(), nullable=True),
        sa.Column('description_en', sa.String(), nullable=True),
        sa.Column('parent_group_id', sa.UUID(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('is_included_in_menu', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['parent_group_id'], ['groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_iiko_id'), 'groups', ['iiko_id'], unique=True)
    
    # 2. Add group_id to products
    op.add_column('products', sa.Column('group_id', sa.UUID(), nullable=True))
    op.create_foreign_key('products_group_id_fkey', 'products', 'groups', ['group_id'], ['id'])
    
    # 3. Drop subcategory_id from products (check if column exists first)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'subcategory_id'
    """))
    if result.fetchone():
        # Drop FK constraint if it exists
        try:
            op.drop_constraint('products_subcategory_id_fkey', 'products', type_='foreignkey')
        except:
            pass  # Constraint may not exist
        op.drop_column('products', 'subcategory_id')
    
    # 4. Drop subcategories table (with CASCADE)
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'subcategories'
    """))
    if result.fetchone():
        op.execute('DROP TABLE IF EXISTS subcategories CASCADE')
    
    # 5. Drop categories table (with CASCADE)
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'categories'
    """))
    if result.fetchone():
        op.execute('DROP TABLE IF EXISTS categories CASCADE')


def downgrade() -> None:
    # Recreate categories table
    op.create_table('categories',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('iiko_id', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_uz', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_ru', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_en', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('organization_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='categories_organization_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='categories_pkey')
    )
    op.create_index('ix_categories_iiko_id', 'categories', ['iiko_id'], unique=True)
    
    # Recreate subcategories table
    op.create_table('subcategories',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('iiko_id', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_uz', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_ru', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name_en', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('category_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='subcategories_category_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='subcategories_pkey')
    )
    op.create_index('ix_subcategories_iiko_id', 'subcategories', ['iiko_id'], unique=True)
    
    # Add subcategory_id back to products
    op.add_column('products', sa.Column('subcategory_id', sa.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('products_subcategory_id_fkey', 'products', 'subcategories', ['subcategory_id'], ['id'])
    
    # Remove group_id from products
    op.drop_constraint('products_group_id_fkey', 'products', type_='foreignkey')
    op.drop_column('products', 'group_id')
    
    # Drop groups table
    op.drop_index(op.f('ix_groups_iiko_id'), table_name='groups')
    op.drop_table('groups')
