"""Add real_cost_usd to credit_transactions

Revision ID: aae8dc883892
Revises: 851d54183b97
Create Date: 2025-05-22 21:37:27.961567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aae8dc883892'
down_revision = '851d54183b97'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add real_cost_usd column to credit_transactions table
    op.add_column('credit_transactions', sa.Column('real_cost_usd', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove the real_cost_usd column
    op.drop_column('credit_transactions', 'real_cost_usd') 