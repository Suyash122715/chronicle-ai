"""PortfolioExtractor — specialized LLM extractor for portfolio documents."""

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


class PortfolioExtractor(BaseLLMExtractor):
    """LLM-based extractor for portfolio artifacts.

    Extends BaseLLMExtractor and implements document-type-specific logic:
    - Target prompt/schema directory: 'portfolio' (backend/prompts/portfolio/)
    - prepare_variables: Supplies document_text, document_type, output_schema
    - post_process: Standardizes owner_info, projects, skills, work_experience,
                    education, certifications, extracts provenance, and records
                    warnings for missing critical fields.

    Fields are grounded in DATABASE.md entities:
    - owner_info   → User + Artifact
    - projects     → Project entity (title, description, github_url, start_date, end_date)
    - skills       → Skill entity (name, category)
    - work_experience → Timeline Event / Relationship
    - education    → Timeline Event / Artifact Metadata
    - certifications → Certifications entity
    """

    DOCUMENT_TYPE_NAME: str = "portfolio"

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
        """Returns prompt folder key for portfolio extraction."""
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
            "owner_info": {
                "name": "",
                "title": "",
                "bio": "",
                "email": "",
                "phone": "",
                "linkedin_url": "",
                "github_url": "",
                "website_url": "",
            },
            "projects": [],
            "skills": [],
            "work_experience": [],
            "education": [],
            "certifications": [],
        }
        provenance_map: dict[str, Provenance] = {}

        if parsed_json is None:
            warnings.append("LLM returned no parsed JSON content.")
            return structured_data, provenance_map, warnings

        # Map owner_info
        if "owner_info" in parsed_json and isinstance(parsed_json["owner_info"], dict):
            structured_data["owner_info"].update(parsed_json["owner_info"])
        else:
            # Flat-structure fallback
            for key in ["name", "title", "bio", "email", "phone",
                        "linkedin_url", "github_url", "website_url"]:
                if key in parsed_json:
                    structured_data["owner_info"][key] = str(parsed_json[key])

        # Validate essential owner_info fields
        owner = structured_data["owner_info"]
        if not owner.get("name"):
            warnings.append("Missing or empty portfolio 'owner name' field.")
        if not owner.get("title"):
            warnings.append("Missing or empty portfolio 'owner title' field.")

        # Map list fields
        for field in ("projects", "skills", "work_experience", "education", "certifications"):
            if field in parsed_json and isinstance(parsed_json[field], list):
                structured_data[field] = parsed_json[field]

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
