"""ResumeExtractor — specialized LLM extractor for resume documents."""

from typing import Any

from app.domain.entities.artifact import Artifact
from app.domain.value_objects.classification_result import ClassificationResult
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.base_extractor import BaseLLMExtractor


class ResumeExtractor(BaseLLMExtractor):
    """LLM-based extractor for resume artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'resume' (backend/prompts/resume/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes skills, education, experience, projects, certifications,
                    extracts provenance, and records warnings for missing fields.
    """

    DOCUMENT_TYPE_NAME: str = "resume"

    def get_document_type_name(self) -> str:
        """Returns prompt folder key for resume extraction."""
        return self.DOCUMENT_TYPE_NAME

    def prepare_variables(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> dict[str, Any]:
        """Provides template variables required for prompt rendering."""
        bundle = self._prompt_repository.get_prompt_bundle(
            document_type=self.DOCUMENT_TYPE_NAME,
            version=self._prompt_version,
        )
        return {
            "document_text": artifact.raw_text or "",
            "document_type": classification_result.document_type.value,
            "output_schema": bundle.output_schema,
        }

    def post_process(
        self,
        parsed_json: dict[str, Any] | None,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> tuple[dict[str, Any], dict[str, Provenance], list[str]]:
        """Converts raw LLM parsed JSON into standardized structured_data, provenance, and warnings."""
        warnings: list[str] = []
        structured_data: dict[str, Any] = {
            "personal_info": {},
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map personal_info / contact_info
        if "personal_info" in parsed_json and isinstance(parsed_json["personal_info"], dict):
            structured_data["personal_info"] = parsed_json["personal_info"]
        elif "contact_info" in parsed_json and isinstance(parsed_json["contact_info"], dict):
            structured_data["personal_info"] = parsed_json["contact_info"]

        # Map skills
        if "skills" in parsed_json and isinstance(parsed_json["skills"], list):
            structured_data["skills"] = parsed_json["skills"]
        else:
            warnings.append("Missing or invalid 'skills' field in LLM response.")

        # Map education
        if "education" in parsed_json and isinstance(parsed_json["education"], list):
            structured_data["education"] = parsed_json["education"]

        # Map experience (check both 'experience' and 'work_experience')
        if "experience" in parsed_json and isinstance(parsed_json["experience"], list):
            structured_data["experience"] = parsed_json["experience"]
        elif "work_experience" in parsed_json and isinstance(parsed_json["work_experience"], list):
            structured_data["experience"] = parsed_json["work_experience"]

        # Map projects
        if "projects" in parsed_json and isinstance(parsed_json["projects"], list):
            structured_data["projects"] = parsed_json["projects"]

        # Map certifications
        if "certifications" in parsed_json and isinstance(parsed_json["certifications"], list):
            structured_data["certifications"] = parsed_json["certifications"]

        # Map provenance from _provenance object if present
        raw_provenance = parsed_json.get("_provenance")
        if isinstance(raw_provenance, dict):
            for field_name, evidence in raw_provenance.items():
                if isinstance(evidence, str):
                    provenance_map[field_name] = Provenance(
                        artifact_id=artifact.id,
                        evidence_snippet=evidence,
                    )
                elif isinstance(evidence, dict):
                    snippet = str(evidence.get("evidence_snippet") or evidence.get("text") or evidence)
                    provenance_map[field_name] = Provenance(
                        artifact_id=artifact.id,
                        evidence_snippet=snippet,
                    )

        return structured_data, provenance_map, warnings
