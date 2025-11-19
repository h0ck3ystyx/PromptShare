"""add_collections_and_faqs_tables

Revision ID: f5281b67fc55
Revises: add_analytics_events
Create Date: 2025-11-18 21:28:35.654123

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = 'f5281b67fc55'
down_revision = 'add_analytics_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_collections_name'), 'collections', ['name'], unique=False)
    op.create_index(op.f('ix_collections_is_featured'), 'collections', ['is_featured'], unique=False)
    op.create_index(op.f('ix_collections_display_order'), 'collections', ['display_order'], unique=False)
    op.create_index(op.f('ix_collections_created_by_id'), 'collections', ['created_by_id'], unique=False)

    # Create collection_prompts table (many-to-many with ordering)
    op.create_table(
        'collection_prompts',
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('collection_id', 'prompt_id')
    )

    # Create FAQs table
    op.create_table(
        'faqs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('question', sa.String(length=500), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faqs_question'), 'faqs', ['question'], unique=False)
    op.create_index(op.f('ix_faqs_category'), 'faqs', ['category'], unique=False)
    op.create_index(op.f('ix_faqs_display_order'), 'faqs', ['display_order'], unique=False)
    op.create_index(op.f('ix_faqs_is_active'), 'faqs', ['is_active'], unique=False)
    op.create_index(op.f('ix_faqs_created_by_id'), 'faqs', ['created_by_id'], unique=False)


def downgrade() -> None:
    # Drop FAQs table
    op.drop_index(op.f('ix_faqs_created_by_id'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_is_active'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_display_order'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_category'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_question'), table_name='faqs')
    op.drop_table('faqs')

    # Drop collection_prompts table
    op.drop_table('collection_prompts')

    # Drop collections table
    op.drop_index(op.f('ix_collections_created_by_id'), table_name='collections')
    op.drop_index(op.f('ix_collections_display_order'), table_name='collections')
    op.drop_index(op.f('ix_collections_is_featured'), table_name='collections')
    op.drop_index(op.f('ix_collections_name'), table_name='collections')
    op.drop_table('collections')
