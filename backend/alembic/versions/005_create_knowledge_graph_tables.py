"""create_knowledge_graph_tables

Revision ID: 005_create_knowledge_graph_tables
Revises: 004_create_artifact_extractions_table
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '005_create_knowledge_graph_tables'
down_revision: Union[str, None] = '004_create_artifact_extractions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create graph_entities table
    op.create_table(
        'graph_entities',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('properties', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'entity_type', 'canonical_name', name='uq_graph_entities_user_type_canonical')
    )
    op.create_index(op.f('ix_graph_entities_user_id'), 'graph_entities', ['user_id'], unique=False)
    op.create_index(op.f('ix_graph_entities_entity_type'), 'graph_entities', ['entity_type'], unique=False)
    op.create_index(op.f('ix_graph_entities_canonical_name'), 'graph_entities', ['canonical_name'], unique=False)

    # 2. Create graph_relationships table
    op.create_table(
        'graph_relationships',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('source_entity_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('target_entity_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('properties', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_entity_id'], ['graph_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['graph_entities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'source_entity_id', 'target_entity_id', 'relationship_type', name='uq_graph_relationships_user_source_target_type')
    )
    op.create_index(op.f('ix_graph_relationships_user_id'), 'graph_relationships', ['user_id'], unique=False)
    op.create_index(op.f('ix_graph_relationships_source_entity_id'), 'graph_relationships', ['source_entity_id'], unique=False)
    op.create_index(op.f('ix_graph_relationships_target_entity_id'), 'graph_relationships', ['target_entity_id'], unique=False)
    op.create_index(op.f('ix_graph_relationships_relationship_type'), 'graph_relationships', ['relationship_type'], unique=False)

    # 3. Create entity_artifact_provenance table
    op.create_table(
        'entity_artifact_provenance',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('entity_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('artifact_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('extraction_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('evidence', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['graph_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['extraction_id'], ['artifact_extractions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_id', 'artifact_id', name='uq_entity_provenance_entity_artifact')
    )
    op.create_index(op.f('ix_entity_artifact_provenance_user_id'), 'entity_artifact_provenance', ['user_id'], unique=False)
    op.create_index(op.f('ix_entity_artifact_provenance_entity_id'), 'entity_artifact_provenance', ['entity_id'], unique=False)
    op.create_index(op.f('ix_entity_artifact_provenance_artifact_id'), 'entity_artifact_provenance', ['artifact_id'], unique=False)
    op.create_index(op.f('ix_entity_artifact_provenance_extraction_id'), 'entity_artifact_provenance', ['extraction_id'], unique=False)

    # 4. Create relationship_artifact_provenance table
    op.create_table(
        'relationship_artifact_provenance',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('relationship_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('artifact_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('extraction_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('evidence', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['relationship_id'], ['graph_relationships.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['extraction_id'], ['artifact_extractions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('relationship_id', 'artifact_id', name='uq_relationship_provenance_rel_artifact')
    )
    op.create_index(op.f('ix_relationship_artifact_provenance_user_id'), 'relationship_artifact_provenance', ['user_id'], unique=False)
    op.create_index(op.f('ix_relationship_artifact_provenance_relationship_id'), 'relationship_artifact_provenance', ['relationship_id'], unique=False)
    op.create_index(op.f('ix_relationship_artifact_provenance_artifact_id'), 'relationship_artifact_provenance', ['artifact_id'], unique=False)
    op.create_index(op.f('ix_relationship_artifact_provenance_extraction_id'), 'relationship_artifact_provenance', ['extraction_id'], unique=False)


def downgrade() -> None:
    # Drop relationship_artifact_provenance
    op.drop_index(op.f('ix_relationship_artifact_provenance_extraction_id'), table_name='relationship_artifact_provenance')
    op.drop_index(op.f('ix_relationship_artifact_provenance_artifact_id'), table_name='relationship_artifact_provenance')
    op.drop_index(op.f('ix_relationship_artifact_provenance_relationship_id'), table_name='relationship_artifact_provenance')
    op.drop_index(op.f('ix_relationship_artifact_provenance_user_id'), table_name='relationship_artifact_provenance')
    op.drop_table('relationship_artifact_provenance')

    # Drop entity_artifact_provenance
    op.drop_index(op.f('ix_entity_artifact_provenance_extraction_id'), table_name='entity_artifact_provenance')
    op.drop_index(op.f('ix_entity_artifact_provenance_artifact_id'), table_name='entity_artifact_provenance')
    op.drop_index(op.f('ix_entity_artifact_provenance_entity_id'), table_name='entity_artifact_provenance')
    op.drop_index(op.f('ix_entity_artifact_provenance_user_id'), table_name='entity_artifact_provenance')
    op.drop_table('entity_artifact_provenance')

    # Drop graph_relationships
    op.drop_index(op.f('ix_graph_relationships_relationship_type'), table_name='graph_relationships')
    op.drop_index(op.f('ix_graph_relationships_target_entity_id'), table_name='graph_relationships')
    op.drop_index(op.f('ix_graph_relationships_source_entity_id'), table_name='graph_relationships')
    op.drop_index(op.f('ix_graph_relationships_user_id'), table_name='graph_relationships')
    op.drop_table('graph_relationships')

    # Drop graph_entities
    op.drop_index(op.f('ix_graph_entities_canonical_name'), table_name='graph_entities')
    op.drop_index(op.f('ix_graph_entities_entity_type'), table_name='graph_entities')
    op.drop_index(op.f('ix_graph_entities_user_id'), table_name='graph_entities')
    op.drop_table('graph_entities')
