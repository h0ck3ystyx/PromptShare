"""add_analytics_events_table

Revision ID: add_analytics_events
Revises: add_follows_notifications
Create Date: 2025-11-19 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_analytics_events'
down_revision = 'add_follows_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    analyticseventtype_enum = postgresql.ENUM(
        'view', 'copy', 'search',
        name='analyticseventtype',
        create_type=False,
    )

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE analyticseventtype AS ENUM ('view', 'copy', 'search');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('event_type', analyticseventtype_enum, nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    
    # Create indexes
    op.create_index(op.f('ix_analytics_events_event_type'), 'analytics_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_analytics_events_prompt_id'), 'analytics_events', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_user_id'), 'analytics_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_created_at'), 'analytics_events', ['created_at'], unique=False)
    
    # Create composite indexes
    op.create_index('ix_analytics_events_type_created', 'analytics_events', ['event_type', 'created_at'], unique=False)
    op.create_index('ix_analytics_events_prompt_type', 'analytics_events', ['prompt_id', 'event_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_analytics_events_prompt_type', table_name='analytics_events')
    op.drop_index('ix_analytics_events_type_created', table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_created_at'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_user_id'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_prompt_id'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_event_type'), table_name='analytics_events')
    
    # Drop table
    op.drop_table('analytics_events')
    
    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS analyticseventtype")
