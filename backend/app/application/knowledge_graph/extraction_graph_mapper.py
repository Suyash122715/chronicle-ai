"""ExtractionGraphMapper — deterministic mapper converting ExtractionResult into Knowledge Graph candidates.

Permitted relationship semantics (V1 authoritative):
    ROLE        → USES        → SKILL / TECHNOLOGY   (explicit in extraction)
    ROLE        → WORKED_AT   → COMPANY               (explicit in extraction)
    PROJECT     → USES        → SKILL / TECHNOLOGY   (explicit in extraction)
    PROJECT     → RELATED_TO  → ROLE                 (ONLY when extraction explicitly associates them)
    CERTIFICATE → CERTIFIED_IN → SKILL / TECHNOLOGY  (explicit in extraction)
    CERTIFICATE → ISSUED_BY   → INSTITUTION / COMPANY (explicit in extraction)

Prohibited relationships (must never be created):
    COMPANY     → USES        → SKILL / TECHNOLOGY   (not a valid extraction relationship)
    Any cross-type SKILL ↔ TECHNOLOGY merge at graph layer

SKILL vs TECHNOLOGY classification:
    Always delegated to the extraction's `category` field.
    If `category` == "skill"       → EntityType.SKILL
    If `category` == "technology"  → EntityType.TECHNOLOGY
    Items without a category field default to EntityType.SKILL for top-level skills lists
    and EntityType.TECHNOLOGY for technology/language lists unless overridden by category.
    An unrecognised explicit category string raises ValueError via _category_to_entity_type().
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType

# Recognised category strings that map to SKILL or TECHNOLOGY.
# All comparisons are case-insensitive after normalisation.
_SKILL_CATEGORIES: frozenset[str] = frozenset(
    {"skill", "skills", "soft skill", "soft_skill", "hard skill", "hard_skill", "competency"}
)
_TECHNOLOGY_CATEGORIES: frozenset[str] = frozenset(
    {
        "technology", "technologies", "tech", "tool", "tools", "framework", "frameworks",
        "library", "libraries", "language", "languages", "platform", "platforms",
        "database", "databases", "infrastructure",
    }
)


def _category_to_entity_type(category: str) -> EntityType:
    """Maps an extraction category string to EntityType.SKILL or EntityType.TECHNOLOGY.

    Args:
        category: Raw category string from the extraction (e.g. "skill", "technology").

    Returns:
        EntityType.SKILL or EntityType.TECHNOLOGY.

    Raises:
        ValueError: If the category string is non-empty and not recognised.
            Empty/None categories are handled by callers with a context-appropriate default.
    """
    normalised = category.strip().lower()
    if normalised in _SKILL_CATEGORIES:
        return EntityType.SKILL
    if normalised in _TECHNOLOGY_CATEGORIES:
        return EntityType.TECHNOLOGY
    raise ValueError(
        f"Unrecognised extraction category '{category}'. "
        f"Recognised skill categories: {sorted(_SKILL_CATEGORIES)}. "
        f"Recognised technology categories: {sorted(_TECHNOLOGY_CATEGORIES)}."
    )


@dataclass
class GraphCandidates:
    """Container holding mapped GraphEntity and GraphRelationship candidates with their respective provenance."""

    entities: list[GraphEntity] = field(default_factory=list)
    relationships: list[GraphRelationship] = field(default_factory=list)
    entity_provenance: dict[UUID, GraphProvenance] = field(default_factory=dict)
    relationship_provenance: dict[UUID, GraphProvenance] = field(default_factory=dict)


class ExtractionGraphMapper:
    """Pure domain/application mapper that deterministically transforms ExtractionResult structured data
    into Knowledge Graph entities and relationships.

    See module docstring for the authoritative permitted/prohibited relationship semantics.
    """

    def map_extraction_to_graph(
        self,
        user_id: UUID,
        artifact_id: UUID,
        extraction_id: UUID | None,
        extraction_result: ExtractionResult,
    ) -> GraphCandidates:
        """Transforms an ExtractionResult into deduplicated GraphEntity, GraphRelationship, and
        GraphProvenance candidates.

        Returns an empty GraphCandidates object if extraction status is FAILED, NOT_SUPPORTED,
        or SKIPPED.
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

        def resolve_skill_or_technology(
            item: Any,
            default_type: EntityType,
            idx: int,
            context_prefix: str,
        ) -> tuple[str | None, EntityType]:
            """Extracts the name and entity type from a skill/technology item.

            Args:
                item: Raw item from extraction (str or dict).
                default_type: Default EntityType when no category is present.
                idx: Index in parent list (for source_loc).
                context_prefix: Source location prefix string.

            Returns:
                Tuple of (name_or_None, resolved_entity_type).
            """
            if isinstance(item, str):
                return item, default_type
            elif isinstance(item, dict):
                name = item.get("name") or item.get("skill") or item.get("technology")
                raw_category = str(item.get("category", "")).strip()
                if raw_category:
                    try:
                        entity_type = _category_to_entity_type(raw_category)
                    except ValueError:
                        # Unrecognised category — re-raise to surface the error
                        raise
                else:
                    entity_type = default_type
                return name, entity_type
            return None, default_type

        # -------------------------------------------------------------
        # 1. TOP-LEVEL SKILLS (Common across Resume, Certificate, Internship, Project, Portfolio)
        #    Default entity type: SKILL (these lists are labelled "skills" by extractors)
        #    Category field overrides the default when present.
        # -------------------------------------------------------------
        skills_raw = data.get("skills", [])
        if isinstance(skills_raw, list):
            for idx, item in enumerate(skills_raw):
                name, entity_type = resolve_skill_or_technology(
                    item, EntityType.SKILL, idx, "skills"
                )
                if name:
                    raw_cat = str(item.get("category", "")).strip() if isinstance(item, dict) else ""
                    get_or_create_entity(
                        entity_type,
                        name,
                        properties={"category": raw_cat} if raw_cat else {},
                        source_loc=f"skills[{idx}]",
                    )

        # -------------------------------------------------------------
        # 2. WORK EXPERIENCE / INTERNSHIPS (Company & Role)
        #    Permitted: ROLE → WORKED_AT → COMPANY
        #    Permitted: ROLE → USES → SKILL / TECHNOLOGY  (from experience-level skill lists)
        #    Prohibited: COMPANY → USES → SKILL / TECHNOLOGY
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

                    # ROLE → WORKED_AT → COMPANY
                    if comp_entity and role_entity:
                        add_relationship(
                            role_entity,
                            comp_entity,
                            RelationshipType.WORKED_AT,
                            source_loc=f"experience[{idx}]",
                        )

                    # ROLE → USES → SKILL / TECHNOLOGY (from experience-level skill list)
                    if role_entity:
                        exp_skills = exp.get("skills") or exp.get("technologies") or []
                        if isinstance(exp_skills, list):
                            for s_idx, s_item in enumerate(exp_skills):
                                s_name, s_type = resolve_skill_or_technology(
                                    s_item, EntityType.SKILL, s_idx,
                                    f"experience[{idx}].skills"
                                )
                                if s_name:
                                    raw_cat = (
                                        str(s_item.get("category", "")).strip()
                                        if isinstance(s_item, dict) else ""
                                    )
                                    skill_ent = get_or_create_entity(
                                        s_type,
                                        s_name,
                                        properties={"category": raw_cat} if raw_cat else {},
                                        source_loc=f"experience[{idx}].skills[{s_idx}]",
                                    )
                                    if skill_ent:
                                        add_relationship(
                                            role_entity,
                                            skill_ent,
                                            RelationshipType.USES,
                                            source_loc=f"experience[{idx}]",
                                        )

                    # PROJECT → RELATED_TO → ROLE: only if extraction explicitly provides
                    # a `role_ref` or `related_role` field on the experience entry.
                    # Never inferred from shared skills, chronology, or proximity.
                    # (No automatic PROJECT → RELATED_TO → ROLE from experience entries.)

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
            # ROLE → WORKED_AT → COMPANY
            if comp_entity and role_entity:
                add_relationship(
                    role_entity,
                    comp_entity,
                    RelationshipType.WORKED_AT,
                    source_loc="internship_info",
                )
            # ROLE → USES → SKILL / TECHNOLOGY from internship skill list
            if role_entity:
                intern_skills = internship_info.get("skills") or []
                if isinstance(intern_skills, list):
                    for s_idx, s_item in enumerate(intern_skills):
                        s_name, s_type = resolve_skill_or_technology(
                            s_item, EntityType.SKILL, s_idx, "internship_info.skills"
                        )
                        if s_name:
                            raw_cat = (
                                str(s_item.get("category", "")).strip()
                                if isinstance(s_item, dict) else ""
                            )
                            skill_ent = get_or_create_entity(
                                s_type,
                                s_name,
                                properties={"category": raw_cat} if raw_cat else {},
                                source_loc=f"internship_info.skills[{s_idx}]",
                            )
                            if skill_ent:
                                add_relationship(
                                    role_entity,
                                    skill_ent,
                                    RelationshipType.USES,
                                    source_loc="internship_info",
                                )

        # -------------------------------------------------------------
        # 3. PROJECTS & TECHNOLOGIES
        #    Permitted: PROJECT → USES → SKILL / TECHNOLOGY
        #    Permitted: PROJECT → RELATED_TO → ROLE  (ONLY when extraction explicitly provides it)
        #    Default entity type for project technology lists: TECHNOLOGY
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
                        # PROJECT → USES → SKILL / TECHNOLOGY
                        techs = proj.get("technologies") or proj.get("technologies_used") or []
                        if isinstance(techs, list):
                            for t_idx, tech_item in enumerate(techs):
                                t_name, t_type = resolve_skill_or_technology(
                                    tech_item, EntityType.TECHNOLOGY, t_idx,
                                    f"projects[{idx}].technologies"
                                )
                                if t_name:
                                    raw_cat = (
                                        str(tech_item.get("category", "")).strip()
                                        if isinstance(tech_item, dict) else ""
                                    )
                                    tech_ent = get_or_create_entity(
                                        t_type,
                                        t_name,
                                        properties={"category": raw_cat} if raw_cat else {},
                                        source_loc=f"projects[{idx}].technologies[{t_idx}]",
                                    )
                                    if tech_ent:
                                        add_relationship(
                                            proj_entity,
                                            tech_ent,
                                            RelationshipType.USES,
                                            source_loc=f"projects[{idx}]",
                                        )

                        # PROJECT → RELATED_TO → ROLE: ONLY when extraction explicitly provides
                        # a `role_ref`, `related_role`, or `role_id` field on the project entry.
                        # Never inferred from shared technologies, chronology, same company, or proximity.
                        explicit_role_ref = (
                            proj.get("role_ref") or proj.get("related_role") or proj.get("role_id")
                        )
                        if explicit_role_ref:
                            role_entity = get_or_create_entity(
                                EntityType.ROLE,
                                explicit_role_ref if isinstance(explicit_role_ref, str) else None,
                                source_loc=f"projects[{idx}].role_ref",
                            )
                            if role_entity:
                                add_relationship(
                                    proj_entity,
                                    role_entity,
                                    RelationshipType.RELATED_TO,
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
                # Technologies list — default TECHNOLOGY
                techs = data.get("technologies", [])
                if isinstance(techs, list):
                    for t_idx, tech_item in enumerate(techs):
                        t_name, t_type = resolve_skill_or_technology(
                            tech_item, EntityType.TECHNOLOGY, t_idx, "technologies"
                        )
                        if t_name:
                            raw_cat = (
                                str(tech_item.get("category", "")).strip()
                                if isinstance(tech_item, dict) else ""
                            )
                            tech_ent = get_or_create_entity(
                                t_type,
                                t_name,
                                properties={"category": raw_cat} if raw_cat else {},
                                source_loc=f"technologies[{t_idx}]",
                            )
                            if tech_ent:
                                add_relationship(
                                    proj_entity,
                                    tech_ent,
                                    RelationshipType.USES,
                                    source_loc="project_info",
                                )

                # Outcomes → Achievements
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
        #    Languages default to TECHNOLOGY entity type.
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
                # Languages → Technology (default TECHNOLOGY)
                langs = data.get("languages", [])
                if isinstance(langs, list):
                    for l_idx, lang_item in enumerate(langs):
                        l_name, l_type = resolve_skill_or_technology(
                            lang_item, EntityType.TECHNOLOGY, l_idx, "languages"
                        )
                        if l_name:
                            raw_cat = (
                                str(lang_item.get("category", "")).strip()
                                if isinstance(lang_item, dict) else ""
                            )
                            tech_ent = get_or_create_entity(
                                l_type,
                                l_name,
                                properties={"category": raw_cat} if raw_cat else {},
                                source_loc=f"languages[{l_idx}]",
                            )
                            if tech_ent:
                                add_relationship(
                                    proj_entity,
                                    tech_ent,
                                    RelationshipType.USES,
                                    source_loc="repository_info",
                                )

        # -------------------------------------------------------------
        # 5. CERTIFICATES & CERTIFICATIONS
        #    Permitted: CERTIFICATE → CERTIFIED_IN → SKILL / TECHNOLOGY
        #    Permitted: CERTIFICATE → ISSUED_BY    → INSTITUTION / COMPANY
        # -------------------------------------------------------------
        certs_raw = data.get("certifications") or []
        if isinstance(certs_raw, list):
            for idx, cert in enumerate(certs_raw):
                if isinstance(cert, dict):
                    c_title = cert.get("title") or cert.get("name")
                    c_issuer = cert.get("issuer") or cert.get("organization")
                    c_issuer_type = cert.get("issuer_type", "")

                    cert_entity = get_or_create_entity(
                        EntityType.CERTIFICATE, c_title, source_loc=f"certifications[{idx}].title"
                    )

                    # CERTIFICATE → ISSUED_BY → INSTITUTION or COMPANY
                    if cert_entity and c_issuer:
                        # Use issuer_type field to determine entity type; default COMPANY
                        issuer_entity_type = EntityType.COMPANY
                        if isinstance(c_issuer_type, str):
                            norm_it = c_issuer_type.strip().lower()
                            if norm_it in {"institution", "university", "school", "college"}:
                                issuer_entity_type = EntityType.INSTITUTION
                        issuer_entity = get_or_create_entity(
                            issuer_entity_type, c_issuer,
                            source_loc=f"certifications[{idx}].issuer"
                        )
                        if issuer_entity:
                            add_relationship(
                                cert_entity,
                                issuer_entity,
                                RelationshipType.ISSUED_BY,
                                source_loc=f"certifications[{idx}]",
                            )

                    # CERTIFICATE → CERTIFIED_IN → SKILL / TECHNOLOGY
                    if cert_entity:
                        cert_skills = cert.get("skills") or cert.get("technologies") or []
                        if isinstance(cert_skills, list):
                            for s_idx, s_item in enumerate(cert_skills):
                                s_name, s_type = resolve_skill_or_technology(
                                    s_item, EntityType.SKILL, s_idx,
                                    f"certifications[{idx}].skills"
                                )
                                if s_name:
                                    raw_cat = (
                                        str(s_item.get("category", "")).strip()
                                        if isinstance(s_item, dict) else ""
                                    )
                                    skill_ent = get_or_create_entity(
                                        s_type,
                                        s_name,
                                        properties={"category": raw_cat} if raw_cat else {},
                                        source_loc=f"certifications[{idx}].skills[{s_idx}]",
                                    )
                                    if skill_ent:
                                        add_relationship(
                                            cert_entity,
                                            skill_ent,
                                            RelationshipType.CERTIFIED_IN,
                                            source_loc=f"certifications[{idx}]",
                                        )

        # Certificate Info object (Certificate Extractor)
        cert_info = data.get("certificate_info")
        if isinstance(cert_info, dict):
            c_title = cert_info.get("title")
            c_issuer = cert_info.get("issuer")
            c_issuer_type = cert_info.get("issuer_type", "")
            cert_entity = get_or_create_entity(
                EntityType.CERTIFICATE, c_title, source_loc="certificate_info.title"
            )

            # CERTIFICATE → ISSUED_BY → INSTITUTION or COMPANY
            if cert_entity and c_issuer:
                issuer_entity_type = EntityType.COMPANY
                if isinstance(c_issuer_type, str):
                    norm_it = c_issuer_type.strip().lower()
                    if norm_it in {"institution", "university", "school", "college"}:
                        issuer_entity_type = EntityType.INSTITUTION
                issuer_entity = get_or_create_entity(
                    issuer_entity_type, c_issuer, source_loc="certificate_info.issuer"
                )
                if issuer_entity:
                    add_relationship(
                        cert_entity,
                        issuer_entity,
                        RelationshipType.ISSUED_BY,
                        source_loc="certificate_info",
                    )

            # CERTIFICATE → CERTIFIED_IN → SKILL / TECHNOLOGY
            if cert_entity:
                cert_skills = cert_info.get("skills") or cert_info.get("technologies") or []
                if isinstance(cert_skills, list):
                    for s_idx, s_item in enumerate(cert_skills):
                        s_name, s_type = resolve_skill_or_technology(
                            s_item, EntityType.SKILL, s_idx, "certificate_info.skills"
                        )
                        if s_name:
                            raw_cat = (
                                str(s_item.get("category", "")).strip()
                                if isinstance(s_item, dict) else ""
                            )
                            skill_ent = get_or_create_entity(
                                s_type,
                                s_name,
                                properties={"category": raw_cat} if raw_cat else {},
                                source_loc=f"certificate_info.skills[{s_idx}]",
                            )
                            if skill_ent:
                                add_relationship(
                                    cert_entity,
                                    skill_ent,
                                    RelationshipType.CERTIFIED_IN,
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
