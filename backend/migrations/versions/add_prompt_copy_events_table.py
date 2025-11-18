"""add_prompt_copy_events_table

Revision ID: add_copy_events
Revises: c4fc3a468ec0
Create Date: 2025-11-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_copy_events'
down_revision = 'c4fc3a468ec0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'prompt_copy_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('copied_at', sa.DateTime(), nullable=False),
        sa.Column('platform_tag', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_prompt_copy_events_prompt_id'), 'prompt_copy_events', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_prompt_copy_events_user_id'), 'prompt_copy_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_prompt_copy_events_copied_at'), 'prompt_copy_events', ['copied_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_prompt_copy_events_copied_at'), table_name='prompt_copy_events')
    op.drop_index(op.f('ix_prompt_copy_events_user_id'), table_name='prompt_copy_events')
    op.drop_index(op.f('ix_prompt_copy_events_prompt_id'), table_name='prompt_copy_events')
    op.drop_table('prompt_copy_events')

