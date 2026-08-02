"""DocumentClassifier abstract domain interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.value_objects.classification_result import ClassificationResult


class DocumentClassifierInterface(ABC):
    """Provider-independent domain interface for document classification.

    This interface must remain decoupled from specific AI or heuristic classification providers.
    """

    @abstractmethod
    async def classify(
        self,
        artifact_id: UUID,
        filename: str,
        mime_type: str,
        file_size: int,
        metadata: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """Classifies a document and returns a structured immutable ClassificationResult.

        Args:
            artifact_id: Unique UUID of the target artifact.
            filename: Original filename of the uploaded artifact.
            mime_type: MIME content type of the file.
            file_size: File size in bytes.
            metadata: Optional dictionary of artifact metadata (e.g. source, checksum).

        Returns:
            An immutable ClassificationResult value object.
        """
        pass
