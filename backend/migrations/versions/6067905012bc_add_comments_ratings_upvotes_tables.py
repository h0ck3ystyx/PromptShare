"""add_comments_ratings_upvotes_tables

Revision ID: 6067905012bc
Revises: add_copy_events
Create Date: 2025-11-17 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6067905012bc'
down_revision = 'add_copy_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create comments table
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ),
    )
    op.create_index(op.f('ix_comments_prompt_id'), 'comments', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_comment_id'), 'comments', ['parent_comment_id'], unique=False)

    # Create ratings table
    op.create_table(
        'ratings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('prompt_id', 'user_id', name='uq_rating_prompt_user'),
    )
    op.create_index(op.f('ix_ratings_prompt_id'), 'ratings', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_ratings_user_id'), 'ratings', ['user_id'], unique=False)

    # Create upvotes table
    op.create_table(
        'upvotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('prompt_id', 'user_id', name='uq_upvote_prompt_user'),
    )
    op.create_index(op.f('ix_upvotes_prompt_id'), 'upvotes', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_upvotes_user_id'), 'upvotes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_upvotes_user_id'), table_name='upvotes')
    op.drop_index(op.f('ix_upvotes_prompt_id'), table_name='upvotes')
    op.drop_table('upvotes')
    
    op.drop_index(op.f('ix_ratings_user_id'), table_name='ratings')
    op.drop_index(op.f('ix_ratings_prompt_id'), table_name='ratings')
    op.drop_table('ratings')
    
    op.drop_index(op.f('ix_comments_parent_comment_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_user_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_prompt_id'), table_name='comments')
    op.drop_table('comments')
