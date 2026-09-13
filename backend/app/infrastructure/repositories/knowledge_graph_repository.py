"""SQLAlchemy 2 implementation of KnowledgeGraphRepositoryInterface."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.exceptions.graph_exceptions import GraphEntityNotFoundError
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
from app.infrastructure.db.models.entity_artifact_provenance_model import EntityArtifactProvenanceModel
from app.infrastructure.db.models.graph_entity_model import GraphEntityModel
from app.infrastructure.db.models.graph_relationship_model import GraphRelationshipModel
from app.infrastructure.db.models.relationship_artifact_provenance_model import RelationshipArtifactProvenanceModel


class SQLAlchemyKnowledgeGraphRepository(KnowledgeGraphRepositoryInterface):
    """Concrete repository using async SQLAlchemy 2 sessions to persist Knowledge Graph entities,
    relationships, and provenance records.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_entity(
        self, entity: GraphEntity, provenance: GraphProvenance | None = None
    ) -> GraphEntity:
        """Persists or updates a GraphEntity domain entity and links provenance if provided.

        Resolves entity semantically by (user_id, entity_type, canonical_name).
        If existing entity is found, reuses its database ID and merges properties.
        """
        async with self._session.begin_nested():
            model = await self._upsert_entity_model(entity)
            if provenance is not None:
                await self._upsert_entity_provenance(
                    entity_id=model.id,
                    user_id=model.user_id,
                    provenance=provenance,
                )
            await self._session.flush()
            await self._session.refresh(model)
            return model.to_domain()

    async def get_entity_by_id(self, entity_id: UUID) -> GraphEntity | None:
        """Retrieves a GraphEntity by its unique UUID."""
        stmt = select(GraphEntityModel).where(GraphEntityModel.id == entity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_entity_by_canonical(
        self, user_id: UUID, entity_type: EntityType, canonical_name: str
    ) -> GraphEntity | None:
        """Retrieves a GraphEntity for a specific user matching entity_type and canonical_name."""
        entity_type_str = (
            entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
        )
        canonical = canonicalize_name(canonical_name)
        stmt = select(GraphEntityModel).where(
            GraphEntityModel.user_id == user_id,
            GraphEntityModel.entity_type == entity_type_str,
            GraphEntityModel.canonical_name == canonical,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_entities_by_user(
        self, user_id: UUID, entity_type: EntityType | None = None
    ) -> list[GraphEntity]:
        """Retrieves all GraphEntities owned by the given user, optionally filtered by entity_type."""
        stmt = select(GraphEntityModel).where(GraphEntityModel.user_id == user_id)
        if entity_type is not None:
            entity_type_str = (
                entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
            )
            stmt = stmt.where(GraphEntityModel.entity_type == entity_type_str)
        stmt = stmt.order_by(GraphEntityModel.canonical_name.asc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [model.to_domain() for model in models]

    async def save_relationship(
        self, relationship: GraphRelationship, provenance: GraphProvenance | None = None
    ) -> GraphRelationship:
        """Persists or updates a GraphRelationship domain entity and links provenance if provided.

        Enforces user ownership on source and target entities.
        Resolves relationship identity by (user_id, source_entity_id, target_entity_id, relationship_type).
        """
        async with self._session.begin_nested():
            await self._validate_relationship_endpoints(
                user_id=relationship.user_id,
                source_id=relationship.source_entity_id,
                target_id=relationship.target_entity_id,
            )
            model = await self._upsert_relationship_model(
                user_id=relationship.user_id,
                source_id=relationship.source_entity_id,
                target_id=relationship.target_entity_id,
                relationship_type=relationship.relationship_type,
                weight=relationship.weight,
                properties=relationship.properties,
                created_at=relationship.created_at,
                updated_at=relationship.updated_at,
                candidate_id=relationship.id,
            )
            if provenance is not None:
                await self._upsert_relationship_provenance(
                    relationship_id=model.id,
                    user_id=model.user_id,
                    provenance=provenance,
                )
            await self._session.flush()
            await self._session.refresh(model)
            return model.to_domain()

    async def get_relationship_by_id(self, relationship_id: UUID) -> GraphRelationship | None:
        """Retrieves a GraphRelationship by its unique UUID."""
        stmt = select(GraphRelationshipModel).where(GraphRelationshipModel.id == relationship_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_user_graph(
        self,
        user_id: UUID,
        artifact_id: UUID | None = None,
        entity_type: EntityType | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        """Retrieves the full subgraph of entities and relationships for a user,
        optionally filtered by artifact provenance or entity_type.
        """
        entity_type_str = (
            entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
            if entity_type is not None
            else None
        )

        if artifact_id is not None:
            # Query entities linked to artifact provenance
            stmt_entities = (
                select(GraphEntityModel)
                .join(
                    EntityArtifactProvenanceModel,
                    EntityArtifactProvenanceModel.entity_id == GraphEntityModel.id,
                )
                .where(
                    GraphEntityModel.user_id == user_id,
                    EntityArtifactProvenanceModel.artifact_id == artifact_id,
                )
            )
            if entity_type_str is not None:
                stmt_entities = stmt_entities.where(GraphEntityModel.entity_type == entity_type_str)

            # Query relationships linked to artifact provenance
            stmt_relationships = (
                select(GraphRelationshipModel)
                .join(
                    RelationshipArtifactProvenanceModel,
                    RelationshipArtifactProvenanceModel.relationship_id == GraphRelationshipModel.id,
                )
                .where(
                    GraphRelationshipModel.user_id == user_id,
                    RelationshipArtifactProvenanceModel.artifact_id == artifact_id,
                )
            )
        else:
            stmt_entities = select(GraphEntityModel).where(GraphEntityModel.user_id == user_id)
            if entity_type_str is not None:
                stmt_entities = stmt_entities.where(GraphEntityModel.entity_type == entity_type_str)

            stmt_relationships = select(GraphRelationshipModel).where(
                GraphRelationshipModel.user_id == user_id
            )

        res_entities = await self._session.execute(stmt_entities)
        entity_models = res_entities.scalars().all()
        entities = [e.to_domain() for e in entity_models]

        res_relationships = await self._session.execute(stmt_relationships)
        relationship_models = res_relationships.scalars().all()

        if entity_type_str is not None and artifact_id is None:
            valid_ids = {e.id for e in entities}
            relationships = [
                r.to_domain()
                for r in relationship_models
                if r.source_entity_id in valid_ids and r.target_entity_id in valid_ids
            ]
        else:
            relationships = [r.to_domain() for r in relationship_models]

        return entities, relationships

    async def delete_entity(self, entity_id: UUID) -> bool:
        """Deletes a graph entity and cascades deletion to associated relationships and provenance."""
        stmt = select(GraphEntityModel).where(GraphEntityModel.id == entity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def delete_provenance_by_artifact_id(self, artifact_id: UUID) -> bool:
        """Deletes graph entity and relationship provenance records associated with an artifact ID."""
        stmt_rel = delete(RelationshipArtifactProvenanceModel).where(
            RelationshipArtifactProvenanceModel.artifact_id == artifact_id
        )
        res_rel = await self._session.execute(stmt_rel)

        stmt_ent = delete(EntityArtifactProvenanceModel).where(
            EntityArtifactProvenanceModel.artifact_id == artifact_id
        )
        res_ent = await self._session.execute(stmt_ent)

        await self._session.flush()
        total_deleted = (res_rel.rowcount or 0) + (res_ent.rowcount or 0)
        return total_deleted > 0

    async def persist_graph(
        self,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
        entity_provenance: dict[UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        """Atomically persists a collection of entities, relationships, and provenance records.

        Execution stages:
        1. Resolve/upsert all candidate entities via semantic identity (user_id, entity_type, canonical_name).
        2. Build candidate UUID -> database entity UUID map.
        3. Resolve/upsert relationships using database entity IDs for foreign keys and unique constraints.
        4. Upsert entity provenance using (resolved_entity_id, artifact_id).
        5. Upsert relationship provenance using (resolved_relationship_id, artifact_id).
        6. Flush and finalize the atomic transaction.
        """
        entity_prov = entity_provenance or {}
        rel_prov = relationship_provenance or {}

        async with self._session.begin_nested():
            # Stage 1 & 2: resolve/upsert entities and map candidate UUID -> database UUID
            id_map: dict[UUID, UUID] = {}
            persisted_entities_map: dict[UUID, GraphEntityModel] = {}

            for entity in entities:
                model = await self._upsert_entity_model(entity)
                id_map[entity.id] = model.id
                persisted_entities_map[model.id] = model

            # Stage 3: resolve/upsert relationships using resolved database entity IDs
            persisted_relationships: list[GraphRelationship] = []
            rel_id_map: dict[UUID, UUID] = {}
            rel_models_map: dict[UUID, GraphRelationshipModel] = {}

            for rel in relationships:
                resolved_source_id = id_map.get(rel.source_entity_id, rel.source_entity_id)
                resolved_target_id = id_map.get(rel.target_entity_id, rel.target_entity_id)

                # Validate user ownership on both endpoints
                await self._validate_relationship_endpoints(
                    user_id=rel.user_id,
                    source_id=resolved_source_id,
                    target_id=resolved_target_id,
                )

                rel_model = await self._upsert_relationship_model(
                    user_id=rel.user_id,
                    source_id=resolved_source_id,
                    target_id=resolved_target_id,
                    relationship_type=rel.relationship_type,
                    weight=rel.weight,
                    properties=rel.properties,
                    created_at=rel.created_at,
                    updated_at=rel.updated_at,
                    candidate_id=rel.id,
                )
                rel_id_map[rel.id] = rel_model.id
                rel_models_map[rel_model.id] = rel_model
                persisted_relationships.append(rel_model.to_domain())

            # Stage 4: upsert entity provenance
            for candidate_id, prov in entity_prov.items():
                if candidate_id in id_map:
                    resolved_entity_id = id_map[candidate_id]
                    entity_model = persisted_entities_map[resolved_entity_id]
                    await self._upsert_entity_provenance(
                        entity_id=resolved_entity_id,
                        user_id=entity_model.user_id,
                        provenance=prov,
                    )

            # Stage 5: upsert relationship provenance
            for candidate_id, prov in rel_prov.items():
                if candidate_id in rel_id_map:
                    resolved_rel_id = rel_id_map[candidate_id]
                    rel_model = rel_models_map[resolved_rel_id]
                    await self._upsert_relationship_provenance(
                        relationship_id=resolved_rel_id,
                        user_id=rel_model.user_id,
                        provenance=prov,
                    )

            # Stage 6: Flush session to ensure all operations within savepoint are staged
            await self._session.flush()

            persisted_entities = [model.to_domain() for model in persisted_entities_map.values()]
            return persisted_entities, persisted_relationships

    async def get_provenance_for_entities(
        self, user_id: UUID, entity_ids: list[UUID]
    ) -> dict[UUID, list[GraphProvenance]]:
        """Retrieves all provenance records for a given list of entity IDs belonging to the user."""
        if not entity_ids:
            return {}

        stmt = select(EntityArtifactProvenanceModel).where(
            EntityArtifactProvenanceModel.user_id == user_id,
            EntityArtifactProvenanceModel.entity_id.in_(entity_ids),
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()

        provenance_map: dict[UUID, list[GraphProvenance]] = {eid: [] for eid in entity_ids}
        for model in models:
            provenance_map[model.entity_id].append(model.to_domain())
        return provenance_map

    async def get_provenance_for_relationships(
        self, user_id: UUID, relationship_ids: list[UUID]
    ) -> dict[UUID, list[GraphProvenance]]:
        """Retrieves all provenance records for a given list of relationship IDs belonging to the user."""
        if not relationship_ids:
            return {}

        stmt = select(RelationshipArtifactProvenanceModel).where(
            RelationshipArtifactProvenanceModel.user_id == user_id,
            RelationshipArtifactProvenanceModel.relationship_id.in_(relationship_ids),
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()

        provenance_map: dict[UUID, list[GraphProvenance]] = {rid: [] for rid in relationship_ids}
        for model in models:
            provenance_map[model.relationship_id].append(model.to_domain())
        return provenance_map

    # -------------------------------------------------------------------------
    # Internal helpers for upsert and validation
    # -------------------------------------------------------------------------


    async def _upsert_entity_model(self, entity: GraphEntity) -> GraphEntityModel:
        """Resolves an entity semantically by (user_id, entity_type, canonical_name) and upserts."""
        entity_type_str = (
            entity.entity_type.value if isinstance(entity.entity_type, EntityType) else str(entity.entity_type)
        )
        canonical = canonicalize_name(entity.canonical_name or entity.name)
        now = datetime.now(timezone.utc)

        stmt = select(GraphEntityModel).where(
            GraphEntityModel.user_id == entity.user_id,
            GraphEntityModel.entity_type == entity_type_str,
            GraphEntityModel.canonical_name == canonical,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GraphEntityModel(
                id=entity.id,
                user_id=entity.user_id,
                entity_type=entity_type_str,
                name=entity.name,
                canonical_name=canonical,
                properties=dict(entity.properties or {}),
                created_at=entity.created_at or now,
                updated_at=entity.updated_at or now,
            )
            self._session.add(model)
            await self._session.flush()
        else:
            # Re-use existing database entity: merge properties, update name and updated_at
            merged_properties = dict(model.properties or {})
            if entity.properties:
                merged_properties.update(entity.properties)
            model.properties = merged_properties
            if entity.name:
                model.name = entity.name
            model.updated_at = now
            await self._session.flush()

        return model

    async def _upsert_relationship_model(
        self,
        user_id: UUID,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType | str,
        weight: float,
        properties: dict[str, Any],
        created_at: datetime | None,
        updated_at: datetime | None,
        candidate_id: UUID | None = None,
    ) -> GraphRelationshipModel:
        """Resolves a relationship by (user_id, source_id, target_id, rel_type) and upserts."""
        rel_type_str = (
            relationship_type.value
            if isinstance(relationship_type, RelationshipType)
            else str(relationship_type)
        )
        now = datetime.now(timezone.utc)

        stmt = select(GraphRelationshipModel).where(
            GraphRelationshipModel.user_id == user_id,
            GraphRelationshipModel.source_entity_id == source_id,
            GraphRelationshipModel.target_entity_id == target_id,
            GraphRelationshipModel.relationship_type == rel_type_str,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GraphRelationshipModel(
                id=candidate_id or uuid4(),
                user_id=user_id,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relationship_type=rel_type_str,
                weight=weight,
                properties=dict(properties or {}),
                created_at=created_at or now,
                updated_at=updated_at or now,
            )
            self._session.add(model)
            await self._session.flush()
        else:
            # Re-use existing database relationship: merge properties, update weight and updated_at
            merged_properties = dict(model.properties or {})
            if properties:
                merged_properties.update(properties)
            model.properties = merged_properties
            model.weight = weight
            model.updated_at = now
            await self._session.flush()

        return model

    async def _upsert_entity_provenance(
        self, entity_id: UUID, user_id: UUID, provenance: GraphProvenance
    ) -> EntityArtifactProvenanceModel:
        """Upserts an entity provenance record matching (entity_id, artifact_id)."""
        evidence_dict = {
            "evidence_snippet": provenance.evidence_snippet,
            "source_location": provenance.source_location,
            "extraction_method": provenance.extraction_method,
            "metadata": provenance.metadata or {},
        }
        stmt = select(EntityArtifactProvenanceModel).where(
            EntityArtifactProvenanceModel.entity_id == entity_id,
            EntityArtifactProvenanceModel.artifact_id == provenance.artifact_id,
        )
        result = await self._session.execute(stmt)
        prov_model = result.scalar_one_or_none()

        if prov_model is None:
            prov_model = EntityArtifactProvenanceModel(
                id=uuid4(),
                user_id=user_id,
                entity_id=entity_id,
                artifact_id=provenance.artifact_id,
                extraction_id=provenance.extraction_id,
                confidence=provenance.confidence,
                evidence=evidence_dict,
                created_at=datetime.now(timezone.utc),
            )
            self._session.add(prov_model)
        else:
            prov_model.confidence = provenance.confidence
            prov_model.evidence = evidence_dict
            prov_model.extraction_id = provenance.extraction_id

        await self._session.flush()
        return prov_model

    async def _upsert_relationship_provenance(
        self, relationship_id: UUID, user_id: UUID, provenance: GraphProvenance
    ) -> RelationshipArtifactProvenanceModel:
        """Upserts a relationship provenance record matching (relationship_id, artifact_id)."""
        evidence_dict = {
            "evidence_snippet": provenance.evidence_snippet,
            "source_location": provenance.source_location,
            "extraction_method": provenance.extraction_method,
            "metadata": provenance.metadata or {},
        }
        stmt = select(RelationshipArtifactProvenanceModel).where(
            RelationshipArtifactProvenanceModel.relationship_id == relationship_id,
            RelationshipArtifactProvenanceModel.artifact_id == provenance.artifact_id,
        )
        result = await self._session.execute(stmt)
        prov_model = result.scalar_one_or_none()

        if prov_model is None:
            prov_model = RelationshipArtifactProvenanceModel(
                id=uuid4(),
                user_id=user_id,
                relationship_id=relationship_id,
                artifact_id=provenance.artifact_id,
                extraction_id=provenance.extraction_id,
                confidence=provenance.confidence,
                evidence=evidence_dict,
                created_at=datetime.now(timezone.utc),
            )
            self._session.add(prov_model)
        else:
            prov_model.confidence = provenance.confidence
            prov_model.evidence = evidence_dict
            prov_model.extraction_id = provenance.extraction_id

        await self._session.flush()
        return prov_model

    async def _validate_relationship_endpoints(
        self, user_id: UUID, source_id: UUID, target_id: UUID
    ) -> None:
        """Validates that source and target entities exist in graph_entities and belong to user_id."""
        stmt = select(GraphEntityModel).where(
            GraphEntityModel.id.in_([source_id, target_id]),
            GraphEntityModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        found_entities = {e.id: e for e in result.scalars().all()}

        if source_id not in found_entities:
            raise GraphEntityNotFoundError(
                f"Source entity {source_id} not found or does not belong to user {user_id}."
            )
        if target_id not in found_entities:
            raise GraphEntityNotFoundError(
                f"Target entity {target_id} not found or does not belong to user {user_id}."
            )
