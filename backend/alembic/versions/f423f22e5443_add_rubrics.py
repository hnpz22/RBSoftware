"""add_rubrics

Revision ID: f423f22e5443
Revises: 8a7610bb6416
Create Date: 2026-04-23 17:33:35.830692

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'f423f22e5443'
down_revision = '8a7610bb6416'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabla de rúbricas (compartida entre training evaluations
    # y academic assignments)
    op.create_table(
        'rubrics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), unique=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Polimórfico: puede pertenecer a una evaluación de training
        # O a una tarea del LMS
        sa.Column(
            'training_evaluation_id',
            sa.Integer(),
            sa.ForeignKey('training_evaluations.id', ondelete='CASCADE'),
            nullable=True,
        ),
        sa.Column(
            'lms_assignment_id',
            sa.Integer(),
            sa.ForeignKey('lms_assignments.id', ondelete='CASCADE'),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Criterios de la rúbrica. Cada criterio tiene N niveles
    op.create_table(
        'rubric_criteria',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), unique=True, nullable=False),
        sa.Column(
            'rubric_id',
            sa.Integer(),
            sa.ForeignKey('rubrics.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Niveles de desempeño por criterio
    # Ej: Excelente, Bueno, Regular, Insuficiente
    op.create_table(
        'rubric_levels',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('public_id', sa.String(36), unique=True, nullable=False),
        sa.Column(
            'criteria_id',
            sa.Integer(),
            sa.ForeignKey('rubric_criteria.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('rubric_levels')
    op.drop_table('rubric_criteria')
    op.drop_table('rubrics')
