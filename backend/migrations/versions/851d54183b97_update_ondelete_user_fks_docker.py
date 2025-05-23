"""update_ondelete_user_fks_docker

Revision ID: 851d54183b97
Revises: 
Create Date: 2025-05-15 17:09:04.363324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '851d54183b97'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('credits', sa.Integer(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('agents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_table('contests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('is_private', sa.Boolean(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('min_votes_required', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('judge_restrictions', sa.Boolean(), nullable=True),
    sa.Column('author_restrictions', sa.Boolean(), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contests_id'), 'contests', ['id'], unique=False)
    op.create_table('credit_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('transaction_type', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('ai_model', sa.String(), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=True),
    sa.Column('model_cost_rate', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_transactions_id'), 'credit_transactions', ['id'], unique=False)
    op.create_table('texts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('author', sa.String(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_texts_id'), 'texts', ['id'], unique=False)
    op.create_table('agent_executions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('agent_id', sa.Integer(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('execution_type', sa.String(), nullable=False),
    sa.Column('model', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('result_id', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('credits_used', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_executions_id'), 'agent_executions', ['id'], unique=False)
    op.create_table('contest_judges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contest_id', sa.Integer(), nullable=False),
    sa.Column('user_judge_id', sa.Integer(), nullable=True),
    sa.Column('agent_judge_id', sa.Integer(), nullable=True),
    sa.Column('assignment_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('has_voted', sa.Boolean(), nullable=True),
    sa.CheckConstraint('(user_judge_id IS NOT NULL AND agent_judge_id IS NULL) OR (user_judge_id IS NULL AND agent_judge_id IS NOT NULL)', name='ck_contest_judge_one_type_only'),
    sa.ForeignKeyConstraint(['agent_judge_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_judge_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('contest_judge_agent_unique', 'contest_judges', ['contest_id', 'agent_judge_id'], unique=True, postgresql_where=sa.text('agent_judge_id IS NOT NULL'))
    op.create_index('contest_judge_user_unique', 'contest_judges', ['contest_id', 'user_judge_id'], unique=True, postgresql_where=sa.text('user_judge_id IS NOT NULL'))
    op.create_index(op.f('ix_contest_judges_id'), 'contest_judges', ['id'], unique=False)
    op.create_table('contest_texts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contest_id', sa.Integer(), nullable=False),
    sa.Column('text_id', sa.Integer(), nullable=False),
    sa.Column('submission_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ranking', sa.Integer(), nullable=True),
    sa.Column('total_points', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['text_id'], ['texts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('contest_text_unique', 'contest_texts', ['contest_id', 'text_id'], unique=True)
    op.create_index(op.f('ix_contest_texts_id'), 'contest_texts', ['id'], unique=False)
    op.create_table('votes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contest_id', sa.Integer(), nullable=False),
    sa.Column('text_id', sa.Integer(), nullable=False),
    sa.Column('contest_judge_id', sa.Integer(), nullable=False),
    sa.Column('agent_execution_id', sa.Integer(), nullable=True),
    sa.Column('text_place', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['agent_execution_id'], ['agent_executions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['contest_judge_id'], ['contest_judges.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['text_id'], ['texts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_votes_agent_execution_id'), 'votes', ['agent_execution_id'], unique=False)
    op.create_index(op.f('ix_votes_contest_judge_id'), 'votes', ['contest_judge_id'], unique=False)
    op.create_index(op.f('ix_votes_id'), 'votes', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_votes_id'), table_name='votes')
    op.drop_index(op.f('ix_votes_contest_judge_id'), table_name='votes')
    op.drop_index(op.f('ix_votes_agent_execution_id'), table_name='votes')
    op.drop_table('votes')
    op.drop_index(op.f('ix_contest_texts_id'), table_name='contest_texts')
    op.drop_index('contest_text_unique', table_name='contest_texts')
    op.drop_table('contest_texts')
    op.drop_index(op.f('ix_contest_judges_id'), table_name='contest_judges')
    op.drop_index('contest_judge_user_unique', table_name='contest_judges', postgresql_where=sa.text('user_judge_id IS NOT NULL'))
    op.drop_index('contest_judge_agent_unique', table_name='contest_judges', postgresql_where=sa.text('agent_judge_id IS NOT NULL'))
    op.drop_table('contest_judges')
    op.drop_index(op.f('ix_agent_executions_id'), table_name='agent_executions')
    op.drop_table('agent_executions')
    op.drop_index(op.f('ix_texts_id'), table_name='texts')
    op.drop_table('texts')
    op.drop_index(op.f('ix_credit_transactions_id'), table_name='credit_transactions')
    op.drop_table('credit_transactions')
    op.drop_index(op.f('ix_contests_id'), table_name='contests')
    op.drop_table('contests')
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.drop_table('agents')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ### 