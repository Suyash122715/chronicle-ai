"""Unit tests for BaseLLMExtractor orchestration pipeline."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.interfaces.prompt_repository import PromptRepositoryInterface
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.llm_response import LLMResponse
from app.domain.value_objects.prompt_bundle import PromptBundle
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.base_extractor import BaseLLMExtractor


# ---------------------------------------------------------------------------
# Fake implementations (no external calls, no Gemini, no I/O)
# ---------------------------------------------------------------------------


class FakePromptRepository(PromptRepositoryInterface):
    """Minimal in-memory prompt repository for testing."""

    def __init__(self, prompt_text: str = "Extract data:\n{{document_text}}") -> None:
        self._prompt_text = prompt_text

    def get_prompt_bundle(self, document_type: str, version: str | None = None) -> PromptBundle:
        return PromptBundle(
            prompt_text=self._prompt_text,
            output_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            prompt_version=version or "v1",
        )


class FakeLLMProvider(LLMProviderInterface):
    """Minimal in-memory LLM provider returning deterministic responses."""

    def __init__(self, parsed_json: dict[str, Any] | None = None, raise_error: bool = False) -> None:
        self._parsed_json = parsed_json or {"name": "Test User", "_provenance": {}}
        self._raise_error = raise_error

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        if self._raise_error:
            raise RuntimeError("Simulated LLM provider failure")
        return LLMResponse(
            raw_response='{"name": "Test User"}',
            parsed_json=self._parsed_json,
            token_usage={"prompt_tokens": 80, "completion_tokens": 30, "total_tokens": 110},
            latency=0.15,
            provider="fake_provider",
            model="fake_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={"estimated_cost_usd": 0.00011},
        )


class ConcreteTestExtractor(BaseLLMExtractor):
    """Minimal concrete subclass implementing prepare_variables() and post_process()."""

    def get_document_type_name(self) -> str:
        return "resume"

    def prepare_variables(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> dict[str, Any]:
        return {"document_text": artifact.raw_text or ""}

    def post_process(
        self,
        parsed_json: dict[str, Any] | None,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> tuple[dict[str, Any], dict[str, Provenance], list[str]]:
        if not parsed_json:
            return {}, {}, ["No parsed JSON returned"]
        provenance_raw = parsed_json.pop("_provenance", {})
        provenance = {
            k: Provenance(artifact_id=artifact.id, evidence_snippet=str(v))
            for k, v in provenance_raw.items()
        }
        return parsed_json, provenance, []


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def make_artifact(raw_text: str = "Jane Doe — Software Engineer") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="resume.pdf",
        stored_filename="stored_resume.pdf",
        file_path="storage/resume.pdf",
        mime_type="application/pdf",
        file_size=2048,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.resume(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_orchestration_pipeline() -> None:
    """Verifies the full pipeline: prompt load → render → LLM call → ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)

    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository(),
        llm_provider=FakeLLMProvider(),
    )

    result = await extractor.extract(artifact, classification)

    assert isinstance(result, ExtractionResult)
    assert result.artifact_id == artifact.id
    assert result.document_type == DocumentType.resume()
    assert result.status == ExtractionStatus.SUCCESS
    assert result.structured_data == {"name": "Test User"}
    assert result.prompt_version == "v1"
    assert result.extractor_version == "1.0.0"
    assert result.warnings == []


@pytest.mark.asyncio
async def test_llm_metadata_populated() -> None:
    """Verifies llm_metadata carries provider, model, finish_reason, tokens, and latency."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository(),
        llm_provider=FakeLLMProvider(),
    )

    result = await extractor.extract(artifact, classification)

    meta = result.llm_metadata
    assert meta["provider"] == "fake_provider"
    assert meta["model"] == "fake_model_v1"
    assert meta["finish_reason"] == "STOP"
    assert meta["token_usage"]["total_tokens"] == 110
    assert meta["estimated_cost_usd"] == 0.00011
    assert "latency_ms" in meta


@pytest.mark.asyncio
async def test_provenance_attached_to_extracted_fields() -> None:
    """Verifies that _provenance from LLM is mapped into ExtractionResult.provenance."""
    artifact = make_artifact()
    classification = make_classification(artifact)

    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository(),
        llm_provider=FakeLLMProvider(
            parsed_json={
                "name": "Alice",
                "_provenance": {"name": "Found in header"},
            }
        ),
    )

    result = await extractor.extract(artifact, classification)

    assert "name" in result.provenance
    assert isinstance(result.provenance["name"], Provenance)
    assert result.provenance["name"].evidence_snippet == "Found in header"


@pytest.mark.asyncio
async def test_provider_failure_produces_failed_extraction_result() -> None:
    """Verifies that LLM provider failure is caught and returned as FAILED ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)

    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository(),
        llm_provider=FakeLLMProvider(raise_error=True),
    )

    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert result.structured_data == {}
    assert result.provenance == {}
    assert result.error_message == "Simulated LLM provider failure"
    assert result.confidence == ConfidenceLevel.LOW
    assert len(result.warnings) == 1
    assert "Extraction failed" in result.warnings[0]


@pytest.mark.asyncio
async def test_explicit_prompt_version_forwarded_to_repository() -> None:
    """Verifies that prompt_version passed to extractor is forwarded to PromptRepository."""
    artifact = make_artifact()
    classification = make_classification(artifact)

    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository(),
        llm_provider=FakeLLMProvider(),
        prompt_version="v2",
    )

    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v2"


@pytest.mark.asyncio
async def test_document_text_injected_into_rendered_prompt() -> None:
    """Verifies that document_text from prepare_variables() appears in the rendered prompt."""
    rendered_prompts: list[str] = []

    class CapturingLLMProvider(LLMProviderInterface):
        async def generate_structured(self, prompt: str, response_schema: dict, **kwargs) -> LLMResponse:
            rendered_prompts.append(prompt)
            return LLMResponse(
                raw_response="{}",
                parsed_json={},
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency=0.0,
                provider="capturing",
                model="capturing",
                finish_reason="STOP",
                prompt_version="v1",
            )

    artifact = make_artifact(raw_text="Python Engineer with 5 years experience")
    classification = make_classification(artifact)

    extractor = ConcreteTestExtractor(
        prompt_repository=FakePromptRepository("Extract data:\n{{document_text}}"),
        llm_provider=CapturingLLMProvider(),
    )

    await extractor.extract(artifact, classification)

    assert len(rendered_prompts) == 1
    assert "Python Engineer with 5 years experience" in rendered_prompts[0]
