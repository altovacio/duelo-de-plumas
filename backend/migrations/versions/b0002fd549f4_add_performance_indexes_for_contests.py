"""add_performance_indexes_for_contests

Revision ID: b0002fd549f4
Revises: ai_debug_logs_001
Create Date: 2025-05-26 13:02:59.434898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0002fd549f4'
down_revision = 'ai_debug_logs_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for contests table
    op.create_index('idx_contests_status', 'contests', ['status'])
    op.create_index('idx_contests_creator_id', 'contests', ['creator_id'])
    op.create_index('idx_contests_created_at', 'contests', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_contests_end_date', 'contests', ['end_date'])
    op.create_index('idx_contests_status_created_at', 'contests', ['status', 'created_at'], postgresql_ops={'created_at': 'DESC'})
    
    # Add indexes for contest_texts table
    op.create_index('idx_contest_texts_contest_id', 'contest_texts', ['contest_id'])
    op.create_index('idx_contest_texts_submission_date', 'contest_texts', ['submission_date'], postgresql_using='btree', postgresql_ops={'submission_date': 'DESC'})
    op.create_index('idx_contest_texts_contest_submission', 'contest_texts', ['contest_id', 'submission_date'], postgresql_ops={'submission_date': 'DESC'})
    op.create_index('idx_contest_texts_ranking', 'contest_texts', ['contest_id', 'ranking'])
    
    # Add indexes for contest_judges table
    op.create_index('idx_contest_judges_contest_id', 'contest_judges', ['contest_id'])
    op.create_index('idx_contest_judges_user_judge_id', 'contest_judges', ['user_judge_id'], postgresql_where=sa.text('user_judge_id IS NOT NULL'))
    op.create_index('idx_contest_judges_agent_judge_id', 'contest_judges', ['agent_judge_id'], postgresql_where=sa.text('agent_judge_id IS NOT NULL'))


def downgrade() -> None:
    # Drop indexes for contest_judges table
    op.drop_index('idx_contest_judges_agent_judge_id', 'contest_judges')
    op.drop_index('idx_contest_judges_user_judge_id', 'contest_judges')
    op.drop_index('idx_contest_judges_contest_id', 'contest_judges')
    
    # Drop indexes for contest_texts table
    op.drop_index('idx_contest_texts_ranking', 'contest_texts')
    op.drop_index('idx_contest_texts_contest_submission', 'contest_texts')
    op.drop_index('idx_contest_texts_submission_date', 'contest_texts')
    op.drop_index('idx_contest_texts_contest_id', 'contest_texts')
    
    # Drop indexes for contests table
    op.drop_index('idx_contests_status_created_at', 'contests')
    op.drop_index('idx_contests_end_date', 'contests')
    op.drop_index('idx_contests_created_at', 'contests')
    op.drop_index('idx_contests_creator_id', 'contests')
    op.drop_index('idx_contests_status', 'contests') 