"""BaseLLMExtractor abstract infrastructure extractor."""

import time
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.interfaces.prompt_repository import PromptRepositoryInterface
from app.domain.services.prompt_renderer import PromptRenderer
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance


EXTRACTOR_VERSION = "1.0.0"


class BaseLLMExtractor(ArtifactExtractorInterface):
    """Abstract base class for all LLM-based artifact extractors.

    Orchestrates the complete extraction pipeline:

        Artifact
          ↓
        load PromptBundle (PromptRepository)
          ↓
        render prompt (PromptRenderer)
          ↓
        call LLM (LLMProviderInterface)
          ↓
        receive LLMResponse
          ↓
        build ExtractionResult

    No document-specific logic.
    No provider-specific logic.
    Concrete subclasses implement: prepare_variables() and post_process().
    """

    def __init__(
        self,
        prompt_repository: PromptRepositoryInterface,
        llm_provider: LLMProviderInterface,
        prompt_renderer: PromptRenderer | None = None,
        prompt_version: str | None = None,
    ) -> None:
        self._prompt_repository = prompt_repository
        self._llm_provider = llm_provider
        self._prompt_renderer = prompt_renderer or PromptRenderer()
        self._prompt_version = prompt_version

    # ------------------------------------------------------------------
    # Subclass contract – implemented by concrete extractors
    # ------------------------------------------------------------------

    @abstractmethod
    def get_document_type_name(self) -> str:
        """Returns the prompt folder name for this extractor (e.g. 'resume', 'certificate')."""
        pass

    @abstractmethod
    def prepare_variables(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> dict[str, Any]:
        """Returns template variables to inject into the rendered prompt.

        At minimum must include 'document_text'.
        Concrete extractors may add document-type-specific variables.
        """
        pass

    @abstractmethod
    def post_process(
        self,
        parsed_json: dict[str, Any] | None,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> tuple[dict[str, Any], dict[str, Provenance], list[str]]:
        """Post-processes the LLM parsed JSON into structured_data, provenance, and warnings.

        Args:
            parsed_json: Parsed JSON dict returned by the LLM, or None on failure.
            artifact: Original Artifact entity.
            classification_result: ClassificationResult for the artifact.

        Returns:
            Tuple of (structured_data, field_provenance, warnings).
        """
        pass

    # ------------------------------------------------------------------
    # Orchestration pipeline – implemented once, shared by all extractors
    # ------------------------------------------------------------------

    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        """Runs the full extraction pipeline and returns a canonical ExtractionResult."""
        started_at = datetime.now(timezone.utc)
        document_type_name = self.get_document_type_name()
        start_time = time.monotonic()

        try:
            bundle = self._prompt_repository.get_prompt_bundle(
                document_type=document_type_name,
                version=self._prompt_version,
            )

            variables = self.prepare_variables(artifact, classification_result)
            rendered = self._prompt_renderer.render(
                bundle=bundle,
                document_type=document_type_name,
                variables=variables,
            )

            llm_response = await self._llm_provider.generate_structured(
                prompt=rendered.rendered_text,
                response_schema=rendered.schema,
                prompt_version=bundle.prompt_version,
            )

            if llm_response.provider == "disabled" or llm_response.finish_reason == "NO_API_KEY":
                latency_ms = (time.monotonic() - start_time) * 1000
                return ExtractionResult(
                    artifact_id=artifact.id,
                    document_type=classification_result.document_type,
                    structured_data={},
                    provenance={},
                    warnings=["LLM extraction skipped: GEMINI_API_KEY is not configured."],
                    confidence=ConfidenceLevel.LOW,
                    extractor_version=EXTRACTOR_VERSION,
                    prompt_version=bundle.prompt_version,
                    llm_metadata={
                        "provider": llm_response.provider,
                        "model": llm_response.model,
                        "finish_reason": llm_response.finish_reason,
                        "latency_ms": round(latency_ms, 2),
                        **llm_response.metadata,
                    },
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    status=ExtractionStatus.SKIPPED,
                    error_message="GEMINI_API_KEY is not configured.",
                )

            structured_data, field_provenance, warnings = self.post_process(
                parsed_json=llm_response.parsed_json,
                artifact=artifact,
                classification_result=classification_result,
            )

            latency_ms = (time.monotonic() - start_time) * 1000

            llm_metadata = {
                "provider": llm_response.provider,
                "model": llm_response.model,
                "finish_reason": llm_response.finish_reason,
                "latency_ms": round(latency_ms, 2),
                "token_usage": llm_response.token_usage,
                **llm_response.metadata,
            }

            return ExtractionResult(
                artifact_id=artifact.id,
                document_type=classification_result.document_type,
                structured_data=structured_data,
                provenance=field_provenance,
                warnings=warnings,
                confidence=classification_result.confidence_level,
                extractor_version=EXTRACTOR_VERSION,
                prompt_version=bundle.prompt_version,
                llm_metadata=llm_metadata,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                status=ExtractionStatus.SUCCESS,
            )

        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.monotonic() - start_time) * 1000
            return ExtractionResult(
                artifact_id=artifact.id,
                document_type=classification_result.document_type,
                structured_data={},
                provenance={},
                warnings=[f"Extraction failed: {exc}"],
                confidence=ConfidenceLevel.LOW,
                extractor_version=EXTRACTOR_VERSION,
                prompt_version=self._prompt_version or "unknown",
                llm_metadata={"latency_ms": round(latency_ms, 2)},
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                status=ExtractionStatus.FAILED,
                error_message=str(exc),
            )
