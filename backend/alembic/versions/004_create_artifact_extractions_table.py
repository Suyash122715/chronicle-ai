"""create_artifact_extractions_table

Revision ID: 004_create_artifact_extractions_table
Revises: 003_add_processing_status_to_artifacts
Create Date: 2026-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004_create_artifact_extractions_table'
down_revision: Union[str, None] = '003_add_processing_status_to_artifacts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'artifact_extractions',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('artifact_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='SUCCESS'),
        sa.Column('structured_data', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('provenance', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('warnings', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('extractor_version', sa.String(length=64), nullable=False, server_default='1.0.0'),
        sa.Column('prompt_version', sa.String(length=32), nullable=False, server_default='v1'),
        sa.Column('llm_metadata', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('error_message', sa.String(length=512), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifact_extractions_artifact_id'), 'artifact_extractions', ['artifact_id'], unique=False)
    op.create_index(op.f('ix_artifact_extractions_status'), 'artifact_extractions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_artifact_extractions_status'), table_name='artifact_extractions')
    op.drop_index(op.f('ix_artifact_extractions_artifact_id'), table_name='artifact_extractions')
    op.drop_table('artifact_extractions')
