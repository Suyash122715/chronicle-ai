"""Unit tests for FileSystemPromptRepository."""

from pathlib import Path
import pytest

from app.domain.value_objects.prompt_bundle import PromptBundle
from app.infrastructure.ai.prompt_repository import FileSystemPromptRepository


@pytest.fixture
def repo(tmp_path: Path) -> FileSystemPromptRepository:
    """Fixture providing a FileSystemPromptRepository targeting a temporary directory structure."""
    resume_dir = tmp_path / "resume"
    resume_dir.mkdir(parents=True)
    (resume_dir / "v1.md").write_text("# Resume Prompt v1\n{artifact_text}", encoding="utf-8")
    (resume_dir / "v2.md").write_text("# Resume Prompt v2\n{artifact_text}", encoding="utf-8")
    (resume_dir / "schema.json").write_text('{"title": "ResumeSchema"}', encoding="utf-8")

    cert_dir = tmp_path / "certificate"
    cert_dir.mkdir(parents=True)
    (cert_dir / "v1.md").write_text("# Certificate Prompt v1", encoding="utf-8")
    (cert_dir / "schema.json").write_text('{"title": "CertSchema"}', encoding="utf-8")

    no_schema_dir = tmp_path / "noschema"
    no_schema_dir.mkdir(parents=True)
    (no_schema_dir / "v1.md").write_text("# No Schema Prompt", encoding="utf-8")

    return FileSystemPromptRepository(base_dir=tmp_path)


def test_load_prompt_explicit_version(repo: FileSystemPromptRepository) -> None:
    content_v1 = repo.load_prompt("resume", version="v1")
    assert "# Resume Prompt v1" in content_v1

    content_v2 = repo.load_prompt("resume", version="v2")
    assert "# Resume Prompt v2" in content_v2


def test_load_prompt_default_resolves_latest(repo: FileSystemPromptRepository) -> None:
    content_latest = repo.load_prompt("resume")
    assert "# Resume Prompt v2" in content_latest


def test_resolve_latest_version(repo: FileSystemPromptRepository) -> None:
    latest_resume = repo.resolve_latest_version("resume")
    assert latest_resume == "v2"

    latest_cert = repo.resolve_latest_version("certificate")
    assert latest_cert == "v1"


def test_load_schema(repo: FileSystemPromptRepository) -> None:
    schema = repo.load_schema("resume")
    assert schema == {"title": "ResumeSchema"}


def test_load_bundle(repo: FileSystemPromptRepository) -> None:
    bundle = repo.load_bundle("resume", version="v1")
    assert isinstance(bundle, PromptBundle)
    assert "# Resume Prompt v1" in bundle.prompt_text
    assert bundle.output_schema == {"title": "ResumeSchema"}
    assert bundle.prompt_version == "v1"

    # Test domain interface alias get_prompt_bundle
    bundle_interface = repo.get_prompt_bundle("resume")
    assert bundle_interface.prompt_version == "v2"


def test_missing_prompt_handling(repo: FileSystemPromptRepository) -> None:
    with pytest.raises(FileNotFoundError, match="Prompt file not found"):
        repo.load_prompt("resume", version="v99")

    with pytest.raises(FileNotFoundError, match="not found"):
        repo.load_prompt("nonexistent_doc_type")


def test_missing_schema_handling(repo: FileSystemPromptRepository) -> None:
    with pytest.raises(FileNotFoundError, match="Schema file not found"):
        repo.load_schema("noschema")

    with pytest.raises(FileNotFoundError, match="not found"):
        repo.load_schema("nonexistent_doc_type")


def test_default_prompts_directory_exists() -> None:
    """Verifies that the actual backend/prompts directory loaded by default contains valid prompt files."""
    default_repo = FileSystemPromptRepository()
    for doc_type in ["resume", "certificate", "project", "portfolio", "internship", "marksheet", "github", "unknown"]:
        bundle = default_repo.load_bundle(doc_type)
        assert isinstance(bundle, PromptBundle)
        assert bundle.prompt_version == "v1"
        assert bundle.prompt_text != ""
        assert isinstance(bundle.output_schema, dict)
