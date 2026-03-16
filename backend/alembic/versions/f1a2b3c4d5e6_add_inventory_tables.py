"""add_inventory_tables

Revision ID: f1a2b3c4d5e6
Revises: d4e8f1a2b3c5
Create Date: 2026-03-15 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'd4e8f1a2b3c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stock_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
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
    )

    op.create_table(
        'inventory_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['location_id'], ['stock_locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'location_id', 'status', name='uq_inv_balance'),
    )
    op.create_index('ix_inventory_balances_product_id', 'inventory_balances', ['product_id'])
    op.create_index('ix_inventory_balances_location_id', 'inventory_balances', ['location_id'])

    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=True),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['location_id'], ['stock_locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inventory_movements_product_id', 'inventory_movements', ['product_id'])
    op.create_index('ix_inventory_movements_location_id', 'inventory_movements', ['location_id'])

    op.create_table(
        'component_inventory_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['component_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['stock_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'component_id', 'location_id', 'status', name='uq_comp_inv_balance'
        ),
    )
    op.create_index(
        'ix_comp_inv_balances_component_id', 'component_inventory_balances', ['component_id']
    )
    op.create_index(
        'ix_comp_inv_balances_location_id', 'component_inventory_balances', ['location_id']
    )

    op.create_table(
        'component_inventory_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=True),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['component_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['stock_locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_comp_inv_movements_component_id',
        'component_inventory_movements',
        ['component_id'],
    )
    op.create_index(
        'ix_comp_inv_movements_location_id',
        'component_inventory_movements',
        ['location_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_comp_inv_movements_location_id', table_name='component_inventory_movements')
    op.drop_index('ix_comp_inv_movements_component_id', table_name='component_inventory_movements')
    op.drop_table('component_inventory_movements')

    op.drop_index('ix_comp_inv_balances_location_id', table_name='component_inventory_balances')
    op.drop_index('ix_comp_inv_balances_component_id', table_name='component_inventory_balances')
    op.drop_table('component_inventory_balances')

    op.drop_index('ix_inventory_movements_location_id', table_name='inventory_movements')
    op.drop_index('ix_inventory_movements_product_id', table_name='inventory_movements')
    op.drop_table('inventory_movements')

    op.drop_index('ix_inventory_balances_location_id', table_name='inventory_balances')
    op.drop_index('ix_inventory_balances_product_id', table_name='inventory_balances')
    op.drop_table('inventory_balances')

    op.drop_table('stock_locations')
