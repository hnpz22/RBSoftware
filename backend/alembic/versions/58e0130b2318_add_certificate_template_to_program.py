"""add_certificate_template_to_program

Revision ID: 58e0130b2318
Revises: f423f22e5443
Create Date: 2026-04-23 18:42:43.764004

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58e0130b2318'
down_revision = 'f423f22e5443'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'training_programs',
        sa.Column('certificate_template_key', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_programs', 'certificate_template_key')
