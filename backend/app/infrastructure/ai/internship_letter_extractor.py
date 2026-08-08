"""InternshipLetterExtractor — specialized LLM extractor for internship letter documents."""

from typing import Any

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.interfaces.prompt_repository import PromptRepositoryInterface
from app.domain.services.prompt_renderer import PromptRenderer
from app.domain.value_objects.classification_result import ClassificationResult
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.base_extractor import BaseLLMExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository
from app.infrastructure.ai.resume_extractor import get_default_llm_provider


class InternshipLetterExtractor(BaseLLMExtractor):
    """LLM-based extractor for internship letter artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'internship' (backend/prompts/internship/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes internship_info, skills, responsibilities, extracts
                    provenance, and records warnings for missing critical fields.
    """

    DOCUMENT_TYPE_NAME: str = "internship"

    def __init__(
        self,
        prompt_repository: PromptRepositoryInterface | None = None,
        llm_provider: LLMProviderInterface | None = None,
        prompt_renderer: PromptRenderer | None = None,
        prompt_version: str | None = None,
    ) -> None:
        repo = prompt_repository or FileSystemPromptRepository()
        provider = llm_provider or get_default_llm_provider()
        super().__init__(
            prompt_repository=repo,
            llm_provider=provider,
            prompt_renderer=prompt_renderer,
            prompt_version=prompt_version,
        )

    def get_document_type_name(self) -> str:
        """Returns prompt folder key for internship letter extraction."""
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
            "internship_info": {
                "intern_name": "",
                "organization": "",
                "role": "",
                "department": "",
                "start_date": "",
                "end_date": "",
                "duration": "",
                "supervisor_name": "",
                "supervisor_designation": "",
                "stipend": "",
                "location": "",
                "letter_type": "unknown",
                "issue_date": "",
            },
            "skills": [],
            "responsibilities": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map internship_info
        if "internship_info" in parsed_json and isinstance(parsed_json["internship_info"], dict):
            info = parsed_json["internship_info"]
            structured_data["internship_info"].update(info)
        else:
            # Fallback: root-level field mapping if LLM returned flat structure
            for key in [
                "intern_name", "organization", "role", "department",
                "start_date", "end_date", "duration", "supervisor_name",
                "supervisor_designation", "stipend", "location", "letter_type", "issue_date",
            ]:
                if key in parsed_json:
                    structured_data["internship_info"][key] = str(parsed_json[key])
            # Common flat-structure aliases
            if "company" in parsed_json:
                structured_data["internship_info"]["organization"] = str(parsed_json["company"])
            if "name" in parsed_json and not structured_data["internship_info"]["intern_name"]:
                structured_data["internship_info"]["intern_name"] = str(parsed_json["name"])

        # Validate essential internship info fields
        info = structured_data["internship_info"]
        if not info.get("intern_name"):
            warnings.append("Missing or empty internship 'intern_name' field.")
        if not info.get("organization"):
            warnings.append("Missing or empty internship 'organization' field.")
        if not info.get("role"):
            warnings.append("Missing or empty internship 'role' field.")

        # Map skills
        if "skills" in parsed_json and isinstance(parsed_json["skills"], list):
            structured_data["skills"] = parsed_json["skills"]

        # Map responsibilities
        if "responsibilities" in parsed_json and isinstance(parsed_json["responsibilities"], list):
            structured_data["responsibilities"] = parsed_json["responsibilities"]

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
                    snippet = str(
                        evidence.get("evidence_snippet") or evidence.get("text") or evidence
                    )
                    provenance_map[field_name] = Provenance(
                        artifact_id=artifact.id,
                        evidence_snippet=snippet,
                    )

        return structured_data, provenance_map, warnings
