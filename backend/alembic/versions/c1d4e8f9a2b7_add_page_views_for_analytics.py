"""add page_views for traffic analytics

Revision ID: c1d4e8f9a2b7
Revises: 895b71db1280
Create Date: 2026-09-28 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d4e8f9a2b7'
down_revision: Union[str, None] = '895b71db1280'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'page_views',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('referrer', sa.String(length=64), nullable=True),
        sa.Column('path', sa.String(length=200), nullable=False),
        sa.Column('user_agent_family', sa.String(length=32), nullable=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_page_views_user_id', 'page_views', ['user_id'])
    op.create_index('ix_page_views_project_id', 'page_views', ['project_id'])
    op.create_index('ix_page_views_referrer', 'page_views', ['referrer'])
    op.create_index('ix_page_views_viewed_at', 'page_views', ['viewed_at'])


def downgrade() -> None:
    op.drop_index('ix_page_views_viewed_at', table_name='page_views')
    op.drop_index('ix_page_views_referrer', table_name='page_views')
    op.drop_index('ix_page_views_project_id', table_name='page_views')
    op.drop_index('ix_page_views_user_id', table_name='page_views')
    op.drop_table('page_views')