"""MarksheetExtractor — specialized LLM extractor for marksheet/transcript documents."""

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


class MarksheetExtractor(BaseLLMExtractor):
    """LLM-based extractor for marksheet and academic transcript artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'marksheet' (backend/prompts/marksheet/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes academic_info, subjects, extracts provenance,
                    and records warnings for missing fields.
    """

    DOCUMENT_TYPE_NAME: str = "marksheet"

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
        """Returns prompt folder key for marksheet extraction."""
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
            "academic_info": {
                "institution": "",
                "student_name": "",
                "roll_number": "",
                "program": "",
                "term": "",
                "cgpa": "",
                "percentage": "",
                "result_status": "",
                "issue_date": "",
            },
            "subjects": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map academic_info
        if "academic_info" in parsed_json and isinstance(parsed_json["academic_info"], dict):
            info = parsed_json["academic_info"]
            structured_data["academic_info"].update(info)
        else:
            # Check root-level fallback fields if LLM returned flat structure
            for key in ["institution", "student_name", "roll_number", "program", "term", "cgpa", "percentage", "gpa", "result_status", "issue_date"]:
                if key in parsed_json:
                    val_key = "cgpa" if key == "gpa" else key
                    structured_data["academic_info"][val_key] = str(parsed_json[key])

        # Validate essential academic info fields
        academic_info = structured_data["academic_info"]
        if not academic_info.get("institution"):
            warnings.append("Missing or empty marksheet 'institution' field.")
        if not academic_info.get("program"):
            warnings.append("Missing or empty marksheet 'program' field.")

        # Map subjects
        if "subjects" in parsed_json and isinstance(parsed_json["subjects"], list):
            structured_data["subjects"] = parsed_json["subjects"]

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
