"""add_program_repository_associations

Revision ID: dc94de4295fe
Revises: 22230ad15a7d
Create Date: 2026-05-05 14:32:12.584684

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'dc94de4295fe'
down_revision = '22230ad15a7d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'program_repository_folders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'program_id',
            sa.Integer(),
            sa.ForeignKey('training_programs.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'folder_id',
            sa.Integer(),
            sa.ForeignKey('repository_folders.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'assigned_by',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('program_id', 'folder_id', name='uq_program_folder'),
    )

    op.create_table(
        'program_repository_files',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'program_id',
            sa.Integer(),
            sa.ForeignKey('training_programs.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'file_id',
            sa.Integer(),
            sa.ForeignKey('repository_files.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'assigned_by',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('program_id', 'file_id', name='uq_program_file'),
    )


def downgrade() -> None:
    op.drop_table('program_repository_files')
    op.drop_table('program_repository_folders')
