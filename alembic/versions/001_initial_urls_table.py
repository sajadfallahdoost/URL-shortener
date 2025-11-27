"""Initial URLs table

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

This migration creates the URLs table based on the database schema
defined in docs/database/database-design.dbml
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create URLs table with all necessary columns and indexes.
    
    Table structure matches database-design.dbml:
    - id: Primary key (auto-increment)
    - original_url: Text (not null, unique)
    - short_code: VARCHAR(5) (not null, unique)
    - created_at: Timestamp (not null, default: now())
    - click_count: BigInt (not null, default: 0)
    - last_accessed_at: Timestamp (nullable)
    """
    # Create URLs table
    op.create_table(
        'urls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('short_code', sa.String(length=5), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'click_count',
            sa.BigInteger(),
            server_default=sa.text('0'),
            nullable=False
        ),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('original_url'),
        sa.UniqueConstraint('short_code'),
        comment='URL mappings table for URL shortener'
    )
    
    # Create indexes for performance
    op.create_index('idx_short_code', 'urls', ['short_code'], unique=True)
    op.create_index('idx_original_url', 'urls', ['original_url'], unique=True)
    op.create_index('idx_short_code_created', 'urls', ['short_code', 'created_at'])
    op.create_index('idx_created_clicks', 'urls', ['created_at', 'click_count'])


def downgrade() -> None:
    """Drop URLs table and all indexes."""
    op.drop_index('idx_created_clicks', table_name='urls')
    op.drop_index('idx_short_code_created', table_name='urls')
    op.drop_index('idx_original_url', table_name='urls')
    op.drop_index('idx_short_code', table_name='urls')
    op.drop_table('urls')

