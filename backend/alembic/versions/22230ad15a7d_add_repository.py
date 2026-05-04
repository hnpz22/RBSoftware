"""add_repository

Revision ID: 22230ad15a7d
Revises: d8538f6b1176
Create Date: 2026-05-04 17:20:10.295683

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '22230ad15a7d'
down_revision = 'd8538f6b1176'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'repository_folders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('repository_folders.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'repository_files',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), nullable=False, unique=True),
        sa.Column('folder_id', sa.Integer(), sa.ForeignKey('repository_folders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('repository_files')
    op.drop_table('repository_folders')
