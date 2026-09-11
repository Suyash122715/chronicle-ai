"""ExtractionGraphMapper — deterministic mapper converting ExtractionResult into Knowledge Graph candidates."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType


@dataclass
class GraphCandidates:
    """Container holding mapped GraphEntity and GraphRelationship candidates with their respective provenance."""

    entities: list[GraphEntity] = field(default_factory=list)
    relationships: list[GraphRelationship] = field(default_factory=list)
    entity_provenance: dict[UUID, GraphProvenance] = field(default_factory=dict)
    relationship_provenance: dict[UUID, GraphProvenance] = field(default_factory=dict)


class ExtractionGraphMapper:
    """Pure domain/application mapper that deterministically transforms ExtractionResult structured data into Knowledge Graph entities and relationships."""

    def map_extraction_to_graph(
        self,
        user_id: UUID,
        artifact_id: UUID,
        extraction_id: UUID | None,
        extraction_result: ExtractionResult,
    ) -> GraphCandidates:
        """Transforms an ExtractionResult into deduplicated GraphEntity, GraphRelationship, and GraphProvenance candidates.

        Returns an empty GraphCandidates object if extraction status is FAILED, NOT_SUPPORTED, or SKIPPED.
        """
        if extraction_result.status in (
            ExtractionStatus.FAILED,
            ExtractionStatus.NOT_SUPPORTED,
            ExtractionStatus.SKIPPED,
        ):
            return GraphCandidates()

        data = extraction_result.structured_data or {}
        confidence_str = (
            extraction_result.confidence.value
            if hasattr(extraction_result.confidence, "value")
            else str(extraction_result.confidence)
        )

        entities_by_key: dict[tuple[EntityType, str], GraphEntity] = {}
        entity_provenance_map: dict[UUID, GraphProvenance] = {}
        relationships: list[GraphRelationship] = []
        relationship_provenance_map: dict[UUID, GraphProvenance] = {}
        relationships_set: set[tuple[UUID, UUID, RelationshipType]] = set()

        def get_or_create_entity(
            entity_type: EntityType,
            raw_name: Any,
            properties: dict[str, Any] | None = None,
            source_loc: str | None = None,
        ) -> GraphEntity | None:
            if not raw_name or not isinstance(raw_name, str):
                return None
            clean_name = raw_name.strip()
            if not clean_name:
                return None
            canonical = canonicalize_name(clean_name)
            if not canonical:
                return None

            key = (entity_type, canonical)
            if key in entities_by_key:
                return entities_by_key[key]

            entity = GraphEntity(
                user_id=user_id,
                entity_type=entity_type,
                name=clean_name,
                canonical_name=canonical,
                properties=properties or {},
            )
            entities_by_key[key] = entity

            # Retrieve evidence snippet from provenance if available
            evidence_snippet = None
            if extraction_result.provenance:
                prov_obj = extraction_result.provenance.get(source_loc or clean_name)
                if prov_obj and hasattr(prov_obj, "evidence_snippet"):
                    evidence_snippet = prov_obj.evidence_snippet

            entity_provenance_map[entity.id] = GraphProvenance(
                artifact_id=artifact_id,
                extraction_id=extraction_id,
                confidence=confidence_str,
                evidence_snippet=evidence_snippet or f"Extracted {entity_type.value}: {clean_name}",
                source_location=source_loc,
                extraction_method="LLM_EXTRACTION",
            )
            return entity

        def add_relationship(
            source_entity: GraphEntity,
            target_entity: GraphEntity,
            rel_type: RelationshipType,
            weight: float = 1.0,
            properties: dict[str, Any] | None = None,
            source_loc: str | None = None,
        ) -> None:
            if source_entity.id == target_entity.id:
                return  # Rejection of self-referential edges

            rel_key = (source_entity.id, target_entity.id, rel_type)
            if rel_key in relationships_set:
                return

            rel = GraphRelationship(
                user_id=user_id,
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relationship_type=rel_type,
                weight=weight,
                properties=properties or {},
            )
            relationships.append(rel)
            relationships_set.add(rel_key)

            relationship_provenance_map[rel.id] = GraphProvenance(
                artifact_id=artifact_id,
                extraction_id=extraction_id,
                confidence=confidence_str,
                evidence_snippet=f"{source_entity.name} --[{rel_type.value}]--> {target_entity.name}",
                source_location=source_loc,
                extraction_method="LLM_EXTRACTION",
            )

        # -------------------------------------------------------------
        # 1. SKILLS (Common across Resume, Certificate, Internship, Project, Portfolio)
        # -------------------------------------------------------------
        skills_raw = data.get("skills", [])
        if isinstance(skills_raw, list):
            for idx, item in enumerate(skills_raw):
                skill_name = None
                category = ""
                if isinstance(item, str):
                    skill_name = item
                elif isinstance(item, dict):
                    skill_name = item.get("name") or item.get("skill")
                    category = str(item.get("category", ""))

                if skill_name:
                    get_or_create_entity(
                        EntityType.SKILL,
                        skill_name,
                        properties={"category": category} if category else {},
                        source_loc=f"skills[{idx}]",
                    )

        # -------------------------------------------------------------
        # 2. WORK EXPERIENCE / INTERNSHIPS (Company & Role)
        # -------------------------------------------------------------
        exp_raw = data.get("experience") or data.get("work_experience") or []
        if isinstance(exp_raw, list):
            for idx, exp in enumerate(exp_raw):
                if isinstance(exp, dict):
                    comp_name = exp.get("company") or exp.get("organization")
                    role_name = exp.get("role") or exp.get("title") or exp.get("designation")

                    comp_entity = get_or_create_entity(
                        EntityType.COMPANY, comp_name, source_loc=f"experience[{idx}].company"
                    )
                    role_entity = get_or_create_entity(
                        EntityType.ROLE, role_name, source_loc=f"experience[{idx}].role"
                    )

                    if comp_entity and role_entity:
                        add_relationship(
                            role_entity,
                            comp_entity,
                            RelationshipType.HELD_ROLE,
                            source_loc=f"experience[{idx}]",
                        )

        # Internship Info object
        internship_info = data.get("internship_info")
        if isinstance(internship_info, dict):
            org_name = internship_info.get("organization")
            role_name = internship_info.get("role")
            comp_entity = get_or_create_entity(
                EntityType.COMPANY, org_name, source_loc="internship_info.organization"
            )
            role_entity = get_or_create_entity(
                EntityType.ROLE, role_name, source_loc="internship_info.role"
            )
            if comp_entity and role_entity:
                add_relationship(
                    role_entity,
                    comp_entity,
                    RelationshipType.HELD_ROLE,
                    source_loc="internship_info",
                )

        # -------------------------------------------------------------
        # 3. PROJECTS & TECHNOLOGIES
        # -------------------------------------------------------------
        projects_raw = data.get("projects") or []
        if isinstance(projects_raw, list):
            for idx, proj in enumerate(projects_raw):
                if isinstance(proj, dict):
                    p_title = proj.get("title") or proj.get("name")
                    p_desc = proj.get("description", "")
                    proj_entity = get_or_create_entity(
                        EntityType.PROJECT,
                        p_title,
                        properties={"description": p_desc} if p_desc else {},
                        source_loc=f"projects[{idx}].title",
                    )
                    if proj_entity:
                        # Project technologies
                        techs = proj.get("technologies") or proj.get("technologies_used") or []
                        if isinstance(techs, list):
                            for t_idx, tech_item in enumerate(techs):
                                if isinstance(tech_item, str):
                                    tech_name = tech_item
                                elif isinstance(tech_item, dict):
                                    tech_name = tech_item.get("name")
                                else:
                                    tech_name = None
                                tech_entity = get_or_create_entity(
                                    EntityType.TECHNOLOGY,
                                    tech_name,
                                    source_loc=f"projects[{idx}].technologies[{t_idx}]",
                                )
                                if tech_entity:
                                    add_relationship(
                                        proj_entity,
                                        tech_entity,
                                        RelationshipType.USES,
                                        source_loc=f"projects[{idx}]",
                                    )

        # Project Info object (Project Report Extractor)
        project_info = data.get("project_info")
        if isinstance(project_info, dict):
            p_title = project_info.get("title") or project_info.get("name")
            p_desc = project_info.get("description", "")
            proj_entity = get_or_create_entity(
                EntityType.PROJECT,
                p_title,
                properties={"description": p_desc} if p_desc else {},
                source_loc="project_info.title",
            )
            if proj_entity:
                # Technologies list
                techs = data.get("technologies", [])
                if isinstance(techs, list):
                    for t_idx, tech_item in enumerate(techs):
                        if isinstance(tech_item, str):
                            tech_name = tech_item
                        elif isinstance(tech_item, dict):
                            tech_name = tech_item.get("name")
                        else:
                            tech_name = None
                        tech_entity = get_or_create_entity(
                            EntityType.TECHNOLOGY,
                            tech_name,
                            source_loc=f"technologies[{t_idx}]",
                        )
                        if tech_entity:
                            add_relationship(
                                proj_entity,
                                tech_entity,
                                RelationshipType.USES,
                                source_loc="project_info",
                            )

                # Outcomes -> Achievements
                outcomes = data.get("outcomes", [])
                if isinstance(outcomes, list):
                    for o_idx, outcome in enumerate(outcomes):
                        if isinstance(outcome, str) and outcome.strip():
                            ach_entity = get_or_create_entity(
                                EntityType.ACHIEVEMENT,
                                outcome,
                                source_loc=f"outcomes[{o_idx}]",
                            )
                            if ach_entity:
                                add_relationship(
                                    proj_entity,
                                    ach_entity,
                                    RelationshipType.CREATED,
                                    source_loc=f"outcomes[{o_idx}]",
                                )

        # -------------------------------------------------------------
        # 4. GITHUB REPOSITORY EXTRACTOR
        # -------------------------------------------------------------
        repo_info = data.get("repository_info")
        if isinstance(repo_info, dict):
            repo_name = repo_info.get("name")
            repo_desc = repo_info.get("description", "")
            repo_url = repo_info.get("url") or repo_info.get("github_url", "")
            proj_entity = get_or_create_entity(
                EntityType.PROJECT,
                repo_name,
                properties={"description": repo_desc, "url": repo_url},
                source_loc="repository_info.name",
            )
            if proj_entity:
                # Languages -> Technology
                langs = data.get("languages", [])
                if isinstance(langs, list):
                    for l_idx, lang_item in enumerate(langs):
                        if isinstance(lang_item, str):
                            lang_name = lang_item
                        elif isinstance(lang_item, dict):
                            lang_name = lang_item.get("name")
                        else:
                            lang_name = None
                        tech_entity = get_or_create_entity(
                            EntityType.TECHNOLOGY,
                            lang_name,
                            source_loc=f"languages[{l_idx}]",
                        )
                        if tech_entity:
                            add_relationship(
                                proj_entity,
                                tech_entity,
                                RelationshipType.USES,
                                source_loc="repository_info",
                            )

        # -------------------------------------------------------------
        # 5. CERTIFICATES & CERTIFICATIONS
        # -------------------------------------------------------------
        certs_raw = data.get("certifications") or []
        if isinstance(certs_raw, list):
            for idx, cert in enumerate(certs_raw):
                if isinstance(cert, dict):
                    c_title = cert.get("title") or cert.get("name")
                    c_issuer = cert.get("issuer") or cert.get("organization")
                    cert_entity = get_or_create_entity(
                        EntityType.CERTIFICATE, c_title, source_loc=f"certifications[{idx}].title"
                    )
                    issuer_entity = get_or_create_entity(
                        EntityType.COMPANY, c_issuer, source_loc=f"certifications[{idx}].issuer"
                    )
                    if cert_entity and issuer_entity:
                        add_relationship(
                            cert_entity,
                            issuer_entity,
                            RelationshipType.ISSUED_BY,
                            source_loc=f"certifications[{idx}]",
                        )

        # Certificate Info object (Certificate Extractor)
        cert_info = data.get("certificate_info")
        if isinstance(cert_info, dict):
            c_title = cert_info.get("title")
            c_issuer = cert_info.get("issuer")
            cert_entity = get_or_create_entity(
                EntityType.CERTIFICATE, c_title, source_loc="certificate_info.title"
            )
            issuer_entity = get_or_create_entity(
                EntityType.COMPANY, c_issuer, source_loc="certificate_info.issuer"
            )
            if cert_entity and issuer_entity:
                add_relationship(
                    cert_entity,
                    issuer_entity,
                    RelationshipType.ISSUED_BY,
                    source_loc="certificate_info",
                )

        # -------------------------------------------------------------
        # 6. EDUCATION & INSTITUTIONS
        # -------------------------------------------------------------
        edu_raw = data.get("education") or []
        if isinstance(edu_raw, list):
            for idx, edu in enumerate(edu_raw):
                if isinstance(edu, dict):
                    inst_name = edu.get("institution") or edu.get("school") or edu.get("university")
                    prog_name = edu.get("program") or edu.get("degree") or edu.get("field_of_study")
                    inst_entity = get_or_create_entity(
                        EntityType.INSTITUTION, inst_name, source_loc=f"education[{idx}].institution"
                    )
                    if prog_name and inst_entity:
                        role_entity = get_or_create_entity(
                            EntityType.ROLE, prog_name, source_loc=f"education[{idx}].program"
                        )
                        if role_entity:
                            add_relationship(
                                role_entity,
                                inst_entity,
                                RelationshipType.STUDIED_AT,
                                source_loc=f"education[{idx}]",
                            )

        # Academic Info object (Marksheet Extractor)
        academic_info = data.get("academic_info")
        if isinstance(academic_info, dict):
            inst_name = academic_info.get("institution")
            prog_name = academic_info.get("program")
            inst_entity = get_or_create_entity(
                EntityType.INSTITUTION, inst_name, source_loc="academic_info.institution"
            )
            if prog_name and inst_entity:
                role_entity = get_or_create_entity(
                    EntityType.ROLE, prog_name, source_loc="academic_info.program"
                )
                if role_entity:
                    add_relationship(
                        role_entity,
                        inst_entity,
                        RelationshipType.STUDIED_AT,
                        source_loc="academic_info",
                    )

        return GraphCandidates(
            entities=list(entities_by_key.values()),
            relationships=relationships,
            entity_provenance=entity_provenance_map,
            relationship_provenance=relationship_provenance_map,
        )
