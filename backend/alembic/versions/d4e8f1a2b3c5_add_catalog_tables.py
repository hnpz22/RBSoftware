"""add_catalog_tables

Revision ID: d4e8f1a2b3c5
Revises: c1f3a2d8e945
Create Date: 2026-03-15 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e8f1a2b3c5'
down_revision = 'c1f3a2d8e945'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column(
            'type',
            sa.Enum('KIT', 'COMPONENT', name='product_type'),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('qr_code', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('cut_file_key', sa.String(length=500), nullable=True),
        sa.Column('cut_file_notes', sa.Text(), nullable=True),
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
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)

    op.create_table(
        'kit_bom_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kit_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['component_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['kit_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kit_id', 'component_id', name='uq_kit_bom_items_pair'),
    )
    op.create_index(op.f('ix_kit_bom_items_component_id'), 'kit_bom_items', ['component_id'], unique=False)
    op.create_index(op.f('ix_kit_bom_items_kit_id'), 'kit_bom_items', ['kit_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kit_bom_items_kit_id'), table_name='kit_bom_items')
    op.drop_index(op.f('ix_kit_bom_items_component_id'), table_name='kit_bom_items')
    op.drop_table('kit_bom_items')
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_table('products')
    op.execute('DROP TYPE IF EXISTS product_type')  # PostgreSQL only — safe no-op on MySQL
