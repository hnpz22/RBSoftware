"""add_after_lesson_id_to_training_evaluation

Revision ID: 8a7610bb6416
Revises: d84ec47a023d
Create Date: 2026-04-23 15:46:29.250492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a7610bb6416'
down_revision = 'd84ec47a023d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'training_evaluations',
        sa.Column('after_lesson_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_training_evaluations_after_lesson_id',
        'training_evaluations',
        'training_lessons',
        ['after_lesson_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_training_evaluations_after_lesson_id',
        'training_evaluations',
        type_='foreignkey',
    )
    op.drop_column('training_evaluations', 'after_lesson_id')
