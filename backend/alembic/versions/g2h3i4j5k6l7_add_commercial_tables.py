"""add_commercial_tables

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-15 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sales_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column(
            'fulfillment_status',
            sa.String(length=20),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=False),
        sa.Column('customer_phone', sa.String(length=30), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('billing_address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('qr_token', sa.String(length=64), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('snapshot_frozen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        sa.UniqueConstraint('qr_token'),
    )
    op.create_index('ix_sales_orders_status', 'sales_orders', ['status'])

    op.create_table(
        'sales_order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('snapshot_name', sa.String(length=255), nullable=True),
        sa.Column('snapshot_sku', sa.String(length=100), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(
            ['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_sales_order_items_order_id', 'sales_order_items', ['sales_order_id']
    )
    op.create_index(
        'ix_sales_order_items_product_id', 'sales_order_items', ['product_id']
    )


def downgrade() -> None:
    op.drop_index('ix_sales_order_items_product_id', table_name='sales_order_items')
    op.drop_index('ix_sales_order_items_order_id', table_name='sales_order_items')
    op.drop_table('sales_order_items')
    op.drop_index('ix_sales_orders_status', table_name='sales_orders')
    op.drop_table('sales_orders')
