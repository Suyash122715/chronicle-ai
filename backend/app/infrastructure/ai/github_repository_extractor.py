"""GitHubRepositoryExtractor — specialized LLM extractor for GitHub repository artifacts."""

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


class GitHubRepositoryExtractor(BaseLLMExtractor):
    """LLM-based extractor for GitHub repository artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'github' (backend/prompts/github/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes repository_info, languages, topics, contributors,
                    outcomes, extracts provenance, and records warnings for missing
                    critical fields.

    Fields are grounded in DATABASE.md entities:
    - repository_info → Project entity (title/name, description, github_url,
                        start_date/created_at, end_date/updated_at)
    - languages       → Entity entity (entity_type=technology, entity_name)
    - topics          → Entity entity (entity_type=tag)
    - contributors    → Relationship entity (WORKED_AT / CREATED_AT)
    - outcomes        → Artifact Metadata (summary, category)
    """

    DOCUMENT_TYPE_NAME: str = "github"

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
        """Returns prompt folder key for GitHub repository extraction."""
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
            "repository_info": {
                "name": "",
                "url": "",
                "owner": "",
                "description": "",
                "primary_language": "",
                "license": "",
                "created_at": "",
                "updated_at": "",
                "demo_url": "",
                "docs_url": "",
            },
            "languages": [],
            "topics": [],
            "contributors": [],
            "outcomes": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map repository_info
        if "repository_info" in parsed_json and isinstance(parsed_json["repository_info"], dict):
            structured_data["repository_info"].update(parsed_json["repository_info"])
        else:
            # Flat-structure fallback — handle common field aliases
            alias_map: dict[str, str] = {
                "repository_name": "name",
                "repo_name": "name",
                "repo_url": "url",
                "github_url": "url",
                "username": "owner",
                "organization": "owner",
            }
            for key in list(structured_data["repository_info"].keys()):
                if key in parsed_json:
                    structured_data["repository_info"][key] = str(parsed_json[key])
            for src, dst in alias_map.items():
                if src in parsed_json and not structured_data["repository_info"].get(dst):
                    structured_data["repository_info"][dst] = str(parsed_json[src])

        # Validate essential repository_info fields
        repo = structured_data["repository_info"]
        if not repo.get("name"):
            warnings.append("Missing or empty repository 'name' field.")
        if not repo.get("description"):
            warnings.append("Missing or empty repository 'description' field.")

        # Map languages — accept both string list and object list
        if "languages" in parsed_json and isinstance(parsed_json["languages"], list):
            normalized_langs: list[dict[str, str]] = []
            for item in parsed_json["languages"]:
                if isinstance(item, str):
                    normalized_langs.append({"name": item, "category": ""})
                elif isinstance(item, dict):
                    normalized_langs.append(item)
            structured_data["languages"] = normalized_langs
        elif "primary_language" in parsed_json and parsed_json["primary_language"]:
            # If only primary language available at root level, create a single entry
            structured_data["languages"] = [
                {"name": str(parsed_json["primary_language"]), "category": "Primary"}
            ]

        # Map topics — accept string list
        if "topics" in parsed_json and isinstance(parsed_json["topics"], list):
            structured_data["topics"] = [str(t) for t in parsed_json["topics"]]

        # Map contributors
        if "contributors" in parsed_json and isinstance(parsed_json["contributors"], list):
            structured_data["contributors"] = parsed_json["contributors"]

        # Map outcomes
        if "outcomes" in parsed_json and isinstance(parsed_json["outcomes"], list):
            structured_data["outcomes"] = [str(o) for o in parsed_json["outcomes"]]

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
