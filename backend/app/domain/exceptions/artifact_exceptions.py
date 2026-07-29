"""Artifact-related domain exceptions."""

from app.domain.exceptions.base import DomainException


class ArtifactNotFoundError(DomainException):
    """Raised when an requested artifact is not found or does not belong to the user."""

    def __init__(self, message: str = "Artifact not found.") -> None:
        super().__init__(message)


class FileTooLargeError(DomainException):
    """Raised when an uploaded file exceeds the maximum allowed size."""

    def __init__(self, message: str = "File size exceeds maximum allowed limit.") -> None:
        super().__init__(message)


class UnsupportedMediaTypeError(DomainException):
    """Raised when an uploaded file type is not supported."""

    def __init__(self, message: str = "Unsupported media type.") -> None:
        super().__init__(message)


class StorageError(DomainException):
    """Raised when an operation on the underlying file storage fails."""

    def __init__(self, message: str = "Storage operation failed.") -> None:
        super().__init__(message)
