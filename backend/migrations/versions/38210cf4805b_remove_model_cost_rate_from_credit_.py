"""Remove model_cost_rate from credit_transactions

Revision ID: 38210cf4805b
Revises: aae8dc883892
Create Date: 2025-05-22 21:57:06.856254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38210cf4805b'
down_revision = 'aae8dc883892'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('credit_transactions', 'model_cost_rate')


def downgrade() -> None:
    op.add_column('credit_transactions', sa.Column('model_cost_rate', sa.Float(), nullable=True)) 