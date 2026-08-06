"""ExtractorFactory domain service."""

from typing import Type

from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum


class ExtractorFactory:
    """Factory responsible for resolving and instantiating ArtifactExtractor instances.

    Encapsulates extractor lookup via ExtractorRegistry and future routing decisions
    (e.g., feature flags, prompt versions, fallback extractors). The execution layer and
    processing pipeline interact only with ExtractorFactory and never know how selection is performed.
    """

    def __init__(self, registry: ExtractorRegistry) -> None:
        self._registry = registry

    def get_extractor(
        self,
        document_type: DocumentType | DocumentTypeEnum | str,
    ) -> ArtifactExtractorInterface | None:
        """Resolves and returns an instantiated ArtifactExtractor for the given document_type.

        Returns None if no extractor is registered for the document type.
        """
        extractor_or_cls = self._registry.get_extractor(document_type)
        if extractor_or_cls is None:
            return None

        if isinstance(extractor_or_cls, type):
            return extractor_or_cls()

        return extractor_or_cls
