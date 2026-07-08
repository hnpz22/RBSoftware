"""add_repository_file_shares

Revision ID: r3s4t5u6v7w8
Revises: q2r3s4t5u6v7
Create Date: 2026-07-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'r3s4t5u6v7w8'
down_revision = 'q2r3s4t5u6v7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'repository_file_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column(
            'scope_type',
            sa.Enum('work_line', 'school', name='sharescopetype'),
            nullable=False,
        ),
        sa.Column(
            'work_line',
            sa.Enum(
                'kuntur', 'kuntur_abierto', 'ecua', 'ecua_2', 'ecua_3',
                'ares', 'robotschool', name='workline',
            ),
            nullable=True,
        ),
        sa.Column('school_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'file_id', 'scope_type', 'work_line', 'school_id',
            name='uq_repository_file_shares_scope',
        ),
    )


def downgrade() -> None:
    op.drop_table('repository_file_shares')
