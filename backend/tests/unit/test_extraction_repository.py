"""Unit tests for ExtractionRepositoryInterface and SQLAlchemyExtractionRepository."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest

from app.domain.interfaces.extraction_repository import ExtractionRepositoryInterface
from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.db.models.artifact_extraction_model import ArtifactExtractionModel
from app.infrastructure.repositories.extraction_repository import SQLAlchemyExtractionRepository


class InMemoryExtractionRepository(ExtractionRepositoryInterface):
    """In-memory reference implementation of ExtractionRepositoryInterface for unit testing and mocks."""

    def __init__(self) -> None:
        self._store: list[ExtractionResult] = []

    async def save(self, extraction_result: ExtractionResult) -> ExtractionResult:
        self._store.append(extraction_result)
        return extraction_result

    async def get_by_artifact_id(self, artifact_id: UUID) -> ExtractionResult | None:
        matching = [r for r in self._store if r.artifact_id == artifact_id]
        if not matching:
            return None
        return sorted(matching, key=lambda r: r.completed_at, reverse=True)[0]

    async def get_all_by_artifact_id(self, artifact_id: UUID) -> list[ExtractionResult]:
        matching = [r for r in self._store if r.artifact_id == artifact_id]
        return sorted(matching, key=lambda r: r.completed_at, reverse=True)

    async def get_by_id(self, extraction_id: UUID) -> ExtractionResult | None:
        for r in self._store:
            if getattr(r, "id", None) == extraction_id or r.artifact_id == extraction_id:
                return r
        return None

    async def delete_by_artifact_id(self, artifact_id: UUID) -> bool:
        initial_len = len(self._store)
        self._store = [r for r in self._store if r.artifact_id != artifact_id]
        return len(self._store) < initial_len


def _create_sample_extraction(
    artifact_id: UUID | None = None,
    status: ExtractionStatus = ExtractionStatus.SUCCESS,
    doc_type: DocumentType | None = None,
    error_message: str | None = None,
) -> ExtractionResult:
    aid = artifact_id or uuid4()
    now = datetime.now(timezone.utc)
    prov = {
        "title": Provenance(artifact_id=aid, evidence_snippet="Sample Title", confidence="HIGH")
    }
    return ExtractionResult(
        artifact_id=aid,
        document_type=doc_type or DocumentType.resume(),
        structured_data={"title": "Sample Title", "items": [1, 2, 3]},
        provenance=prov,
        warnings=["Test warning"] if status != ExtractionStatus.SUCCESS else [],
        confidence=ConfidenceLevel.HIGH,
        extractor_version="1.0.0",
        prompt_version="v1",
        llm_metadata={"provider": "mock", "latency_ms": 120.5},
        started_at=now,
        completed_at=now,
        status=status,
        error_message=error_message,
    )


@pytest.mark.asyncio
async def test_in_memory_repository_crud() -> None:
    """Verifies InMemoryExtractionRepository satisfies interface contract and basic CRUD operations."""
    repo = InMemoryExtractionRepository()
    artifact_id = uuid4()

    # Initially empty
    assert await repo.get_by_artifact_id(artifact_id) is None
    assert await repo.get_all_by_artifact_id(artifact_id) == []

    # Save initial success result
    result1 = _create_sample_extraction(artifact_id=artifact_id, status=ExtractionStatus.SUCCESS)
    saved1 = await repo.save(result1)
    assert saved1.artifact_id == artifact_id
    assert saved1.status == ExtractionStatus.SUCCESS

    # Query latest
    latest = await repo.get_by_artifact_id(artifact_id)
    assert latest is not None
    assert latest.status == ExtractionStatus.SUCCESS
    assert latest.structured_data == {"title": "Sample Title", "items": [1, 2, 3]}

    # Save secondary failed result
    result2 = _create_sample_extraction(
        artifact_id=artifact_id,
        status=ExtractionStatus.FAILED,
        error_message="LLM extraction timeout",
    )
    await repo.save(result2)

    # Query all
    all_results = await repo.get_all_by_artifact_id(artifact_id)
    assert len(all_results) == 2

    # Delete
    deleted = await repo.delete_by_artifact_id(artifact_id)
    assert deleted is True
    assert await repo.get_by_artifact_id(artifact_id) is None
    assert await repo.get_all_by_artifact_id(artifact_id) == []

    # Delete non-existent
    assert await repo.delete_by_artifact_id(artifact_id) is False


@pytest.mark.asyncio
async def test_sqlalchemy_repository_save_success() -> None:
    """Verifies SQLAlchemyExtractionRepository.save correctly maps domain object and adds to session."""
    session = AsyncMock()
    session.add = MagicMock()
    repo = SQLAlchemyExtractionRepository(session)

    extraction = _create_sample_extraction(status=ExtractionStatus.SUCCESS)

    saved = await repo.save(extraction)

    assert session.add.called
    assert session.flush.called
    assert session.refresh.called
    added_model = session.add.call_args[0][0]
    assert isinstance(added_model, ArtifactExtractionModel)
    assert added_model.artifact_id == extraction.artifact_id
    assert added_model.status == "SUCCESS"
    assert added_model.document_type == "Resume"
    assert added_model.confidence == "HIGH"
    assert issubclass(type(saved), ExtractionResult)
    assert saved.artifact_id == extraction.artifact_id
    assert saved.status == ExtractionStatus.SUCCESS


@pytest.mark.asyncio
async def test_sqlalchemy_repository_save_failed_and_skipped() -> None:
    """Verifies SQLAlchemyExtractionRepository.save preserves FAILED and SKIPPED status and error_message."""
    session = AsyncMock()
    session.add = MagicMock()
    repo = SQLAlchemyExtractionRepository(session)

    # 1. FAILED extraction
    failed_extraction = _create_sample_extraction(
        status=ExtractionStatus.FAILED,
        error_message="Rate limit exceeded",
    )
    saved_failed = await repo.save(failed_extraction)
    added_model_failed = session.add.call_args[0][0]
    assert added_model_failed.status == "FAILED"
    assert added_model_failed.error_message == "Rate limit exceeded"
    assert saved_failed.status == ExtractionStatus.FAILED
    assert saved_failed.error_message == "Rate limit exceeded"

    # 2. SKIPPED extraction
    skipped_extraction = _create_sample_extraction(
        status=ExtractionStatus.SKIPPED,
        error_message="Document unparseable or empty",
    )
    saved_skipped = await repo.save(skipped_extraction)
    added_model_skipped = session.add.call_args[0][0]
    assert added_model_skipped.status == "SKIPPED"
    assert added_model_skipped.error_message == "Document unparseable or empty"
    assert saved_skipped.status == ExtractionStatus.SKIPPED


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_by_artifact_id() -> None:
    """Verifies SQLAlchemyExtractionRepository.get_by_artifact_id executes query and returns domain object."""
    session = AsyncMock()
    repo = SQLAlchemyExtractionRepository(session)
    artifact_id = uuid4()

    # Case 1: Record found
    sample_extraction = _create_sample_extraction(artifact_id=artifact_id)
    model = ArtifactExtractionModel.from_domain(sample_extraction)

    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_execute_result

    result = await repo.get_by_artifact_id(artifact_id)

    assert result is not None
    assert result.artifact_id == artifact_id
    assert result.document_type == DocumentType.resume()
    assert result.status == ExtractionStatus.SUCCESS
    assert session.execute.called

    # Case 2: Record not found
    mock_execute_result.scalar_one_or_none.return_value = None
    not_found = await repo.get_by_artifact_id(uuid4())
    assert not_found is None


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_all_by_artifact_id() -> None:
    """Verifies SQLAlchemyExtractionRepository.get_all_by_artifact_id retrieves all matching records."""
    session = AsyncMock()
    repo = SQLAlchemyExtractionRepository(session)
    artifact_id = uuid4()

    sample1 = _create_sample_extraction(artifact_id=artifact_id, status=ExtractionStatus.SUCCESS)
    sample2 = _create_sample_extraction(artifact_id=artifact_id, status=ExtractionStatus.PARTIAL)
    models = [
        ArtifactExtractionModel.from_domain(sample1),
        ArtifactExtractionModel.from_domain(sample2),
    ]

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = models
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_execute_result

    results = await repo.get_all_by_artifact_id(artifact_id)

    assert len(results) == 2
    assert results[0].artifact_id == artifact_id
    assert results[0].status == ExtractionStatus.SUCCESS
    assert results[1].status == ExtractionStatus.PARTIAL


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_by_id() -> None:
    """Verifies SQLAlchemyExtractionRepository.get_by_id retrieves an extraction record by primary key."""
    session = AsyncMock()
    repo = SQLAlchemyExtractionRepository(session)
    extraction_id = uuid4()
    sample = _create_sample_extraction()
    model = ArtifactExtractionModel.from_domain(sample)
    model.id = extraction_id

    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_execute_result

    result = await repo.get_by_id(extraction_id)

    assert result is not None
    assert result.artifact_id == sample.artifact_id

    # Non-existent ID
    mock_execute_result.scalar_one_or_none.return_value = None
    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_sqlalchemy_repository_delete_by_artifact_id() -> None:
    """Verifies SQLAlchemyExtractionRepository.delete_by_artifact_id performs deletion and returns boolean status."""
    session = AsyncMock()
    repo = SQLAlchemyExtractionRepository(session)
    artifact_id = uuid4()

    # Case 1: Rows deleted
    mock_result_deleted = MagicMock()
    mock_result_deleted.rowcount = 2
    session.execute.return_value = mock_result_deleted

    deleted = await repo.delete_by_artifact_id(artifact_id)
    assert deleted is True
    assert session.flush.called

    # Case 2: No rows deleted
    mock_result_empty = MagicMock()
    mock_result_empty.rowcount = 0
    session.execute.return_value = mock_result_empty

    deleted_empty = await repo.delete_by_artifact_id(artifact_id)
    assert deleted_empty is False
