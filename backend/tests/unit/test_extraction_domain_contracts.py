"""Unit tests for Prompt domain contracts, LLMProviderInterface, and ArtifactExtractorInterface."""

import inspect
from uuid import uuid4

import pytest

from app.domain.entities.artifact import Artifact
from app.domain.interfaces import (
    ArtifactExtractorInterface,
    LLMProviderInterface,
    PromptRepositoryInterface,
)
from app.domain.value_objects import (
    ClassificationResult,
    ConfidenceLevel,
    DocumentType,
    ExtractionResult,
    LLMResponse,
    PromptBundle,
    Provenance,
)
from app.infrastructure.processing.placeholders import BasePlaceholderExtractor


class DummyLLMProvider(LLMProviderInterface):
    """Concrete provider stub for testing LLMProviderInterface contract."""

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> LLMResponse:
        return LLMResponse(
            raw_response='{"key": "value"}',
            parsed_json={"key": "value"},
            token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            latency=0.1,
            provider="dummy",
            model="dummy-model",
            finish_reason="STOP",
            prompt_version=prompt_version,
        )


class DummyPromptRepository(PromptRepositoryInterface):
    """Concrete prompt repository stub for testing PromptRepositoryInterface contract."""

    def get_prompt_bundle(self, document_type: str, version: str | None = None) -> PromptBundle:
        resolved_version = version or "v1"
        return PromptBundle(
            prompt_text=f"Prompt for {document_type}",
            output_schema={"type": "object"},
            prompt_version=resolved_version,
        )


def test_prompt_bundle_creation_and_repository_contract() -> None:
    repo = DummyPromptRepository()
    bundle = repo.get_prompt_bundle("resume", version="v2")

    assert bundle.prompt_text == "Prompt for resume"
    assert bundle.output_schema == {"type": "object"}
    assert bundle.prompt_version == "v2"
    assert bundle.to_dict() == {
        "prompt_text": "Prompt for resume",
        "output_schema": {"type": "object"},
        "prompt_version": "v2",
    }


@pytest.mark.asyncio
async def test_llm_provider_interface_provider_independence() -> None:
    provider = DummyLLMProvider()
    response = await provider.generate_structured(
        prompt="Extract entities",
        response_schema={"type": "object"},
        prompt_version="v1",
    )

    assert isinstance(response, LLMResponse)
    assert response.provider == "dummy"
    assert response.parsed_json == {"key": "value"}


@pytest.mark.asyncio
async def test_artifact_extractor_interface_compatibility() -> None:
    extractor = BasePlaceholderExtractor()
    assert isinstance(extractor, ArtifactExtractorInterface)

    artifact = Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="resume.pdf",
        stored_filename="stored_resume.pdf",
        file_path="storage/resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    classification = ClassificationResult(
        document_type=DocumentType.resume(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="1.0",
        classified_at=artifact.created_at,
        provenance=Provenance(artifact_id=artifact.id),
    )

    result = await extractor.extract(artifact, classification)
    assert isinstance(result, ExtractionResult)
    assert result.artifact_id == artifact.id
    assert result.document_type == DocumentType.resume()
