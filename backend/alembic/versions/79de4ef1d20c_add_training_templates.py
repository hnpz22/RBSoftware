"""add_training_templates

Revision ID: 79de4ef1d20c
Revises: 58e0130b2318
Create Date: 2026-04-23 20:06:46.276750

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '79de4ef1d20c'
down_revision = '58e0130b2318'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'training_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), unique=True, nullable=False),
        sa.Column(
            'program_id',
            sa.Integer(),
            sa.ForeignKey('training_programs.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column(
            'uploaded_by',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('training_templates')
