"""ArtifactExtractor abstract domain interface."""

from abc import ABC, abstractmethod

from app.domain.entities.artifact import Artifact
from app.domain.value_objects.classification_result import ClassificationResult
from app.domain.value_objects.extraction_result import ExtractionResult


class ArtifactExtractorInterface(ABC):
    """Provider-independent domain interface for artifact extraction."""

    @abstractmethod
    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        """Extracts structured domain data from an artifact given its classification result.

        Args:
            artifact: Target domain Artifact entity.
            classification_result: Classification result value object for the artifact.

        Returns:
            An ExtractionResult value object.
        """
        pass
