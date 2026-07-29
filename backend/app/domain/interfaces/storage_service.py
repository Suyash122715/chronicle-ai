"""Storage service interface definition.

Placing the interface in the domain layer ensures business use cases can store/retrieve
files without depending directly on concrete storage providers (e.g. Local Disk, Cloudflare R2, AWS S3).
"""

from abc import ABC, abstractmethod


class StorageServiceInterface(ABC):
    """Abstract interface defining file storage operations."""

    @abstractmethod
    async def save_file(self, file_bytes: bytes, destination_filename: str) -> str:
        """Saves raw file bytes to storage under destination_filename.

        Args:
            file_bytes: Raw binary content of the file.
            destination_filename: Unique filename to save under.

        Returns:
            str: Relative or absolute path/key where the file is stored.

        Raises:
            StorageError: If the file cannot be written.
        """
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> bytes | None:
        """Retrieves raw binary content of a stored file.

        Args:
            file_path: Path/key returned by save_file.

        Returns:
            bytes | None: Binary content if found, None otherwise.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes a file from storage.

        Args:
            file_path: Path/key of the file to remove.

        Returns:
            bool: True if deleted, False if file did not exist.
        """
        pass
