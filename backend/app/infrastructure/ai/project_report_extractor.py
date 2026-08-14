"""ProjectReportExtractor — specialized LLM extractor for project report documents."""

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


class ProjectReportExtractor(BaseLLMExtractor):
    """LLM-based extractor for project report artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'project' (backend/prompts/project/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes project_info, authors, technologies, outcomes,
                    skills, extracts provenance, and records warnings for missing fields.
    """

    DOCUMENT_TYPE_NAME: str = "project"

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
        """Returns prompt folder key for project report extraction."""
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
            "project_info": {
                "title": "",
                "description": "",
                "domain": "",
                "team_name": "",
                "start_date": "",
                "end_date": "",
                "github_url": "",
                "demo_url": "",
                "objective": "",
            },
            "authors": [],
            "technologies": [],
            "outcomes": [],
            "skills": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map project_info
        if "project_info" in parsed_json and isinstance(parsed_json["project_info"], dict):
            structured_data["project_info"].update(parsed_json["project_info"])
        else:
            # Flat-structure fallback
            for key in ["title", "description", "domain", "team_name", "start_date",
                        "end_date", "github_url", "demo_url", "objective"]:
                if key in parsed_json:
                    structured_data["project_info"][key] = str(parsed_json[key])
            # Common aliases
            if "project_name" in parsed_json and not structured_data["project_info"]["title"]:
                structured_data["project_info"]["title"] = str(parsed_json["project_name"])
            if "summary" in parsed_json and not structured_data["project_info"]["description"]:
                structured_data["project_info"]["description"] = str(parsed_json["summary"])

        # Validate essential fields
        info = structured_data["project_info"]
        if not info.get("title"):
            warnings.append("Missing or empty project 'title' field.")
        if not info.get("description"):
            warnings.append("Missing or empty project 'description' field.")

        # Map list fields
        if "authors" in parsed_json and isinstance(parsed_json["authors"], list):
            structured_data["authors"] = parsed_json["authors"]

        if "technologies" in parsed_json and isinstance(parsed_json["technologies"], list):
            raw_techs = parsed_json["technologies"]
            # Accept both string list and object list
            normalized: list[dict[str, str]] = []
            for item in raw_techs:
                if isinstance(item, str):
                    normalized.append({"name": item, "category": ""})
                elif isinstance(item, dict):
                    normalized.append(item)
            structured_data["technologies"] = normalized

        if "outcomes" in parsed_json and isinstance(parsed_json["outcomes"], list):
            structured_data["outcomes"] = parsed_json["outcomes"]

        if "skills" in parsed_json and isinstance(parsed_json["skills"], list):
            structured_data["skills"] = parsed_json["skills"]

        # Map provenance
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
