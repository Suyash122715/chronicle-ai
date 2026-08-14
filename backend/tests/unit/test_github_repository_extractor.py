"""Unit tests for GitHubRepositoryExtractor with mocked LLM provider."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.services.extractor_factory import ExtractorFactory
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.llm_response import LLMResponse
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.github_repository_extractor import GitHubRepositoryExtractor
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class MockLLMProvider(LLMProviderInterface):
    """Mock LLM Provider returning canned GitHub repository extraction responses."""

    def __init__(
        self,
        canned_json: dict[str, Any] | None = None,
        raise_error: bool = False,
        is_disabled: bool = False,
    ) -> None:
        self.canned_json = canned_json if canned_json is not None else {
            "repository_info": {
                "name": "chronicle-ai",
                "url": "https://github.com/example/chronicle-ai",
                "owner": "example",
                "description": "AI-powered professional document intelligence platform.",
                "primary_language": "Python",
                "license": "MIT",
                "created_at": "2024-01-15",
                "updated_at": "2025-06-30",
                "demo_url": "https://chronicle.ai",
                "docs_url": "https://docs.chronicle.ai",
            },
            "languages": [
                {"name": "Python", "category": "Primary"},
                {"name": "TypeScript", "category": "Frontend"},
                {"name": "SQL", "category": "Database"},
            ],
            "topics": ["ai", "fastapi", "llm", "document-extraction", "postgresql"],
            "contributors": [
                {"username": "janesmith", "role": "Lead Developer"},
                {"username": "bobdev", "role": "ML Engineer"},
            ],
            "outcomes": [
                "1.2k GitHub stars",
                "Used in production by 500+ users",
                "95% extraction accuracy on benchmark dataset",
            ],
            "_provenance": {
                "name": "Repository title: chronicle-ai",
                "description": "About section: AI-powered professional document intelligence platform.",
                "topics": "Topics section listing: ai, fastapi, llm, document-extraction, postgresql",
            },
        }
        self.raise_error = raise_error
        self.is_disabled = is_disabled

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        if self.raise_error:
            raise RuntimeError("LLM provider mock error during GitHub repository extraction")

        if self.is_disabled:
            return LLMResponse(
                raw_response="",
                parsed_json=None,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency=0.0,
                provider="disabled",
                model="none",
                finish_reason="NO_API_KEY",
                prompt_version=prompt_version,
                metadata={"warning": "GEMINI_API_KEY is not configured."},
            )

        return LLMResponse(
            raw_response=str(self.canned_json),
            parsed_json=self.canned_json,
            token_usage={"prompt_tokens": 250, "completion_tokens": 130, "total_tokens": 380},
            latency=0.40,
            provider="mock_provider",
            model="mock_model_v1",
            finish_reason="STOP",
            prompt_version=prompt_version,
            metadata={},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_artifact(raw_text: str = "chronicle-ai — GitHub Repository Export") -> Artifact:
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        filename="github_repo.pdf",
        stored_filename="stored_github_repo.pdf",
        file_path="storage/github_repo.pdf",
        mime_type="application/pdf",
        file_size=4096,
        raw_text=raw_text,
    )


def make_classification(artifact: Artifact) -> ClassificationResult:
    return ClassificationResult(
        document_type=DocumentType.github_repository(),
        confidence_level=ConfidenceLevel.HIGH,
        classifier_version="deterministic-1.0",
        classified_at=datetime.now(timezone.utc),
        provenance=Provenance(artifact_id=artifact.id),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_github_repository_extractor_successful_structured_extraction() -> None:
    """Verifies successful structured extraction for GitHub repository artifacts."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    data = result.structured_data

    info = data["repository_info"]
    assert info["name"] == "chronicle-ai"
    assert info["url"] == "https://github.com/example/chronicle-ai"
    assert info["owner"] == "example"
    assert info["primary_language"] == "Python"
    assert info["license"] == "MIT"
    assert info["demo_url"] == "https://chronicle.ai"

    assert len(data["languages"]) == 3
    assert data["languages"][0]["name"] == "Python"
    assert data["languages"][0]["category"] == "Primary"

    assert len(data["topics"]) == 5
    assert "fastapi" in data["topics"]

    assert len(data["contributors"]) == 2
    assert data["contributors"][0]["username"] == "janesmith"

    assert len(data["outcomes"]) == 3
    assert "1.2k GitHub stars" in data["outcomes"]


@pytest.mark.asyncio
async def test_github_repository_extractor_prompt_version() -> None:
    """Verifies that the correct prompt version is returned in ExtractionResult."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_github_repository_extractor_provenance() -> None:
    """Verifies that field-level provenance is correctly mapped from _provenance."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider()

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert "name" in result.provenance
    assert "chronicle-ai" in result.provenance["name"].evidence_snippet
    assert result.provenance["name"].artifact_id == artifact.id

    assert "description" in result.provenance
    assert "AI-powered" in result.provenance["description"].evidence_snippet

    assert "topics" in result.provenance
    assert "fastapi" in result.provenance["topics"].evidence_snippet


@pytest.mark.asyncio
async def test_github_repository_extractor_provider_failure() -> None:
    """Verifies that LLM provider failure returns ExtractionStatus.FAILED with error message."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(raise_error=True)

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.FAILED
    assert result.error_message is not None
    assert "LLM provider mock error during GitHub repository extraction" in result.error_message
    assert len(result.warnings) > 0
    assert "Extraction failed" in result.warnings[0]


@pytest.mark.asyncio
async def test_github_repository_extractor_disabled_provider_returns_skipped() -> None:
    """Verifies missing API key (disabled provider) returns ExtractionStatus.SKIPPED, never SUCCESS."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(is_disabled=True)

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SKIPPED
    assert result.error_message == "GEMINI_API_KEY is not configured."
    assert any("GEMINI_API_KEY is not configured" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_github_repository_extractor_registry_resolution() -> None:
    """Verifies GitHubRepositoryExtractor registration and lookup via ExtractorRegistry."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo_store = FileSystemPromptRepository()
    extractor_instance = GitHubRepositoryExtractor(prompt_repository=repo_store, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.GITHUB_REPOSITORY, extractor_instance)
    resolved = registry.get_extractor(DocumentType.github_repository())

    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_github_repository_extractor_factory_resolution() -> None:
    """Verifies GitHubRepositoryExtractor resolution via ExtractorFactory."""
    registry = ExtractorRegistry()
    mock_provider = MockLLMProvider()
    repo_store = FileSystemPromptRepository()
    extractor_instance = GitHubRepositoryExtractor(prompt_repository=repo_store, llm_provider=mock_provider)

    registry.register(DocumentTypeEnum.GITHUB_REPOSITORY, extractor_instance)
    factory = ExtractorFactory(registry)

    resolved = factory.get_extractor(DocumentType.github_repository())
    assert resolved is not None
    assert resolved == extractor_instance


@pytest.mark.asyncio
async def test_github_repository_extractor_flat_structure_fallback() -> None:
    """Verifies post_process handles flat-structure LLM responses with field aliases."""
    flat_json: dict[str, Any] = {
        "repository_name": "my-ml-project",
        "github_url": "https://github.com/user/my-ml-project",
        "username": "user",
        "description": "A machine learning project for image classification.",
        "primary_language": "Python",
        "topics": ["python", "ml", "cnn"],
        "languages": ["Python", "Jupyter Notebook"],
        "contributors": [],
        "outcomes": ["Achieved 97% test accuracy"],
        "_provenance": {
            "name": "Title: my-ml-project",
        },
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=flat_json)

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    info = result.structured_data["repository_info"]
    assert info["name"] == "my-ml-project"
    assert info["url"] == "https://github.com/user/my-ml-project"
    assert info["owner"] == "user"

    # String languages should be normalised to dicts
    langs = result.structured_data["languages"]
    assert len(langs) == 2
    assert all(isinstance(lang, dict) for lang in langs)
    assert langs[0]["name"] == "Python"
    assert langs[0]["category"] == ""

    assert result.structured_data["topics"] == ["python", "ml", "cnn"]
    assert result.structured_data["outcomes"] == ["Achieved 97% test accuracy"]


@pytest.mark.asyncio
async def test_github_repository_extractor_missing_name_produces_warning() -> None:
    """Verifies a missing repository name produces a warning but status remains SUCCESS."""
    json_without_name: dict[str, Any] = {
        "repository_info": {
            "name": "",
            "description": "Some repo without a name.",
        },
        "languages": [],
        "topics": [],
        "contributors": [],
        "outcomes": [],
        "_provenance": {},
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=json_without_name)

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    assert any("'name'" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_github_repository_extractor_empty_parsed_json_returns_warning() -> None:
    """Verifies empty/None parsed_json produces a warning and empty structured_data fields."""
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json={})

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    # Manually test post_process with None
    structured_data, provenance_map, warnings = extractor.post_process(
        parsed_json=None,
        artifact=artifact,
        classification_result=classification,
    )

    assert "LLM returned no parsed JSON content." in warnings
    assert structured_data["repository_info"]["name"] == ""
    assert provenance_map == {}


@pytest.mark.asyncio
async def test_github_repository_extractor_dict_provenance_parsing() -> None:
    """Verifies evidence provided as dict object in _provenance is correctly parsed into Provenance."""
    dict_prov_json: dict[str, Any] = {
        "repository_info": {
            "name": "dict-prov-repo",
            "description": "Repo with dict provenance.",
        },
        "_provenance": {
            "name": {"evidence_snippet": "Found in title block"},
            "description": {"text": "Found in README description"},
            "topics": {"other_key": "raw dict value"},
        },
    }
    artifact = make_artifact()
    classification = make_classification(artifact)
    repo = FileSystemPromptRepository()
    mock_provider = MockLLMProvider(canned_json=dict_prov_json)

    extractor = GitHubRepositoryExtractor(prompt_repository=repo, llm_provider=mock_provider)
    result = await extractor.extract(artifact, classification)

    assert result.status == ExtractionStatus.SUCCESS
    assert result.provenance["name"].evidence_snippet == "Found in title block"
    assert result.provenance["description"].evidence_snippet == "Found in README description"
    assert "raw dict value" in str(result.provenance["topics"].evidence_snippet)
