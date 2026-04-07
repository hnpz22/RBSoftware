"""add_pdf_annotations

Revision ID: 2be09450964a
Revises: 086159e95965
Create Date: 2026-04-07 14:21:50.070035

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql



# revision identifiers, used by Alembic.
revision = '2be09450964a'
down_revision = '086159e95965'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('pdf_annotations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.Integer(), nullable=False),
    sa.Column('highlights', mysql.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['material_id'], ['lms_materials.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id'),
    sa.UniqueConstraint('user_id', 'material_id', name='uq_pdf_annotations_user_material')
    )


def downgrade() -> None:
    op.drop_table('pdf_annotations')
