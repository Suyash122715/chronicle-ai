"""Local file system implementation of StorageServiceInterface."""

from pathlib import Path
import anyio

from app.config import settings
from app.domain.exceptions.artifact_exceptions import StorageError
from app.domain.interfaces.storage_service import StorageServiceInterface


class LocalStorageService(StorageServiceInterface):
    """Local disk storage service storing files under configured STORAGE_DIR."""

    def __init__(self, storage_dir: str | None = None) -> None:
        self.base_dir = Path(storage_dir or settings.STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_bytes: bytes, destination_filename: str) -> str:
        """Saves binary content to base_dir / destination_filename asynchronously."""
        try:
            target_path = self.base_dir / destination_filename
            async with await anyio.open_file(target_path, "wb") as f:
                await f.write(file_bytes)
            return str(target_path.as_posix())
        except Exception as exc:
            raise StorageError(f"Failed to save file to local storage: {str(exc)}")

    async def get_file(self, file_path: str) -> bytes | None:
        """Reads binary content from file_path asynchronously."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None
        try:
            async with await anyio.open_file(path, "rb") as f:
                return await f.read()
        except Exception as exc:
            raise StorageError(f"Failed to read file from local storage: {str(exc)}")

    async def delete_file(self, file_path: str) -> bool:
        """Deletes file from local storage asynchronously."""
        path = Path(file_path)
        if not path.exists():
            return False
        try:
            path.unlink()
            return True
        except Exception as exc:
            raise StorageError(f"Failed to delete file from local storage: {str(exc)}")
