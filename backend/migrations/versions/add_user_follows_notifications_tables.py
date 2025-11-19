"""add_user_follows_notifications_tables

Revision ID: add_follows_notifications
Revises: 6067905012bc
Create Date: 2025-11-18 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_follows_notifications'
down_revision = '6067905012bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notificationtype enum if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationtype AS ENUM ('new_prompt', 'comment', 'update');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create user_follows table
    op.create_table(
        'user_follows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'category_id', name='uq_user_category_follow'),
    )
    op.create_index(op.f('ix_user_follows_user_id'), 'user_follows', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_follows_category_id'), 'user_follows', ['category_id'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('new_prompt', 'comment', 'update', name='notificationtype'), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_prompt_id'), 'notifications', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_prompt_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_user_follows_category_id'), table_name='user_follows')
    op.drop_index(op.f('ix_user_follows_user_id'), table_name='user_follows')
    op.drop_table('user_follows')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS notificationtype")

