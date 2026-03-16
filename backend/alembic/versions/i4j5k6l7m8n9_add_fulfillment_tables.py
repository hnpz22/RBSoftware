"""add_fulfillment_tables

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-03-15 00:00:05.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i4j5k6l7m8n9'
down_revision = 'h3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sales_order_pack_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('required_qty', sa.Integer(), nullable=False),
        sa.Column(
            'confirmed_qty',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
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
        sa.ForeignKeyConstraint(
            ['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index(
        'ix_so_pack_items_sales_order_id', 'sales_order_pack_items', ['sales_order_id']
    )
    op.create_index(
        'ix_so_pack_items_product_id', 'sales_order_pack_items', ['product_id']
    )

    op.create_table(
        'sales_order_pack_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('scanned_qr', sa.String(length=255), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_so_pack_events_sales_order_id', 'sales_order_pack_events', ['sales_order_id']
    )


def downgrade() -> None:
    op.drop_index('ix_so_pack_events_sales_order_id', table_name='sales_order_pack_events')
    op.drop_table('sales_order_pack_events')

    op.drop_index('ix_so_pack_items_product_id', table_name='sales_order_pack_items')
    op.drop_index('ix_so_pack_items_sales_order_id', table_name='sales_order_pack_items')
    op.drop_table('sales_order_pack_items')
