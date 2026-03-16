"""add_production_tables

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-03-15 00:00:04.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h3i4j5k6l7m8'
down_revision = 'g2h3i4j5k6l7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'production_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cutoff_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_production_batches_status', 'production_batches', ['status'])

    op.create_table(
        'production_batch_sales_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('link_mode', sa.String(length=10), nullable=False),
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
        sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id', 'sales_order_id', name='uq_batch_sales_order'),
    )
    op.create_index(
        'ix_prod_batch_so_batch_id', 'production_batch_sales_orders', ['batch_id']
    )
    op.create_index(
        'ix_prod_batch_so_order_id', 'production_batch_sales_orders', ['sales_order_id']
    )

    op.create_table(
        'production_batch_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('required_qty_total', sa.Integer(), nullable=False),
        sa.Column(
            'available_stock_qty',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        sa.Column('to_produce_qty', sa.Integer(), nullable=False),
        sa.Column(
            'produced_qty', sa.Integer(), nullable=False, server_default=sa.text('0')
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
        sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_prod_batch_items_batch_id', 'production_batch_items', ['batch_id'])
    op.create_index(
        'ix_prod_batch_items_product_id', 'production_batch_items', ['product_id']
    )

    op.create_table(
        'production_item_counters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_item_id', sa.Integer(), nullable=False),
        sa.Column('counted_by', sa.Integer(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['batch_item_id'], ['production_batch_items.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['counted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_prod_item_counters_batch_item_id',
        'production_item_counters',
        ['batch_item_id'],
    )

    op.create_table(
        'production_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_item_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('missing_qty', sa.Integer(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
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
            ['batch_item_id'], ['production_batch_items.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['component_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_production_blocks_batch_item_id', 'production_blocks', ['batch_item_id']
    )
    op.create_index(
        'ix_production_blocks_component_id', 'production_blocks', ['component_id']
    )


def downgrade() -> None:
    op.drop_index('ix_production_blocks_component_id', table_name='production_blocks')
    op.drop_index('ix_production_blocks_batch_item_id', table_name='production_blocks')
    op.drop_table('production_blocks')

    op.drop_index(
        'ix_prod_item_counters_batch_item_id', table_name='production_item_counters'
    )
    op.drop_table('production_item_counters')

    op.drop_index('ix_prod_batch_items_product_id', table_name='production_batch_items')
    op.drop_index('ix_prod_batch_items_batch_id', table_name='production_batch_items')
    op.drop_table('production_batch_items')

    op.drop_index('ix_prod_batch_so_order_id', table_name='production_batch_sales_orders')
    op.drop_index('ix_prod_batch_so_batch_id', table_name='production_batch_sales_orders')
    op.drop_table('production_batch_sales_orders')

    op.drop_index('ix_production_batches_status', table_name='production_batches')
    op.drop_table('production_batches')
