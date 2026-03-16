"""add_created_by_to_sales_orders

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-03-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sales_orders', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sales_orders_created_by_users',
        'sales_orders', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_sales_orders_created_by', 'sales_orders', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_sales_orders_created_by', table_name='sales_orders')
    op.drop_constraint('fk_sales_orders_created_by_users', 'sales_orders', type_='foreignkey')
    op.drop_column('sales_orders', 'created_by')
