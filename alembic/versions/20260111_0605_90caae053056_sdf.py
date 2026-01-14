"""sdf

Revision ID: 90caae053056
Revises: 
Create Date: 2026-01-11 06:05:42.885638

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '90caae053056'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums if they don't exist
    userrole = postgresql.ENUM('ADMIN', 'USER', name='userrole', create_type=False)
    language = postgresql.ENUM('UZBEK', 'RUSSIAN', 'ENGLISH', name='language', create_type=False)
    
    # Check and create enum types
    conn = op.get_bind()
    
    # Create userrole if not exists
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'userrole'"))
    if not result.fetchone():
        userrole.create(conn, checkfirst=True)
    
    # Create language if not exists  
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'language'"))
    if not result.fetchone():
        language.create(conn, checkfirst=True)
    
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('phone_number', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('role', userrole, nullable=False),
    sa.Column('current_lang', language, nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_table('users')

