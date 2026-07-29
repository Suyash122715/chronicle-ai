"""add_processing_status_to_artifacts

Revision ID: 003_add_processing_status_to_artifacts
Revises: 002_create_artifacts_table
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_processing_status_to_artifacts'
down_revision: Union[str, None] = '002_create_artifacts_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('artifacts', sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'))
    op.add_column('artifacts', sa.Column('raw_text', sa.Text(), nullable=True))
    op.add_column('artifacts', sa.Column('error_message', sa.String(length=512), nullable=True))
    op.add_column('artifacts', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_artifacts_status'), 'artifacts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_artifacts_status'), table_name='artifacts')
    op.drop_column('artifacts', 'retry_count')
    op.drop_column('artifacts', 'error_message')
    op.drop_column('artifacts', 'raw_text')
    op.drop_column('artifacts', 'status')
