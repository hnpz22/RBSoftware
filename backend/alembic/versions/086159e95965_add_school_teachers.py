"""add_school_teachers

Revision ID: 086159e95965
Revises: l7m8n9o0p1q2
Create Date: 2026-03-31 20:00:47.426395

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '086159e95965'
down_revision = 'l7m8n9o0p1q2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('school_teachers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('school_id', 'user_id', name='uq_school_teachers_school_user')
    )


def downgrade() -> None:
    op.drop_table('school_teachers')
