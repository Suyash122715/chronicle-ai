"""Unit tests for LocalStorageService."""

import tempfile
from pathlib import Path
import pytest

from app.infrastructure.storage.local_storage_service import LocalStorageService


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.mark.asyncio
async def test_save_get_and_delete_file(temp_storage_dir: str) -> None:
    """Verifies file saving, retrieving, and deletion in LocalStorageService."""
    service = LocalStorageService(storage_dir=temp_storage_dir)

    filename = "test_doc.pdf"
    content = b"%PDF-1.4 Fake PDF Content"

    # Save
    saved_path = await service.save_file(content, filename)
    assert Path(saved_path).exists()

    # Get
    retrieved_content = await service.get_file(saved_path)
    assert retrieved_content == content

    # Delete
    deleted = await service.delete_file(saved_path)
    assert deleted is True
    assert not Path(saved_path).exists()

    # Get non-existent
    assert await service.get_file(saved_path) is None


@pytest.mark.asyncio
async def test_delete_non_existent_file_returns_false(temp_storage_dir: str) -> None:
    """Deleting a non-existent file path returns False."""
    service = LocalStorageService(storage_dir=temp_storage_dir)
    fake_path = str(Path(temp_storage_dir) / "non_existent.pdf")
    assert await service.delete_file(fake_path) is False
