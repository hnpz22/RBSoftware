"""add_integration_sync_state

Revision ID: j5k6l7m8n9o0
Revises: i4j5k6l7m8n9
Create Date: 2026-03-15 00:00:06.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n9o0'
down_revision = 'i4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'integration_sync_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_name', sa.String(length=100), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_cursor', sa.String(length=255), nullable=True),
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='NEVER',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('integration_name'),
    )
    op.create_index(
        'ix_integration_sync_states_name',
        'integration_sync_states',
        ['integration_name'],
    )


def downgrade() -> None:
    op.drop_index('ix_integration_sync_states_name', table_name='integration_sync_states')
    op.drop_table('integration_sync_states')
