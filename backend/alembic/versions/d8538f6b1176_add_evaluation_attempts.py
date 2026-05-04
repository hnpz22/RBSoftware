"""add_evaluation_attempts

Revision ID: d8538f6b1176
Revises: 79de4ef1d20c
Create Date: 2026-04-23 20:31:28.700335

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'd8538f6b1176'
down_revision = '79de4ef1d20c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'training_evaluations',
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
    )
    op.add_column(
        'training_submissions',
        sa.Column('attempts_used', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('training_submissions', 'attempts_used')
    op.drop_column('training_evaluations', 'max_attempts')
