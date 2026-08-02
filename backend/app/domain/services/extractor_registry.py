"""ExtractorRegistry domain service."""

from typing import Type

from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum


class ExtractorRegistry:
    """Pure registry mapping DocumentTypes to extractor types.

    Contains zero business logic, conditional execution, or if/else extraction chains.
    Pure dictionary lookup only.
    """

    def __init__(self, default_extractor: Type[ArtifactExtractorInterface] | None = None) -> None:
        self._registry: dict[DocumentTypeEnum, Type[ArtifactExtractorInterface]] = {}
        self._default_extractor = default_extractor

    def register(
        self,
        document_type: DocumentType | DocumentTypeEnum | str,
        extractor_cls: Type[ArtifactExtractorInterface],
    ) -> None:
        """Registers an extractor class for the given DocumentType."""
        enum_val = self._normalize_key(document_type)
        self._registry[enum_val] = extractor_cls

    def get_extractor(
        self,
        document_type: DocumentType | DocumentTypeEnum | str,
    ) -> Type[ArtifactExtractorInterface] | None:
        """Retrieves registered extractor class for document type, returning None if unregistered."""
        enum_val = self._normalize_key(document_type)
        return self._registry.get(enum_val)

    def resolve(
        self,
        document_type: DocumentType | DocumentTypeEnum | str,
    ) -> Type[ArtifactExtractorInterface]:
        """Resolves registered extractor for document type, falling back to default_extractor if unregistered."""
        enum_val = self._normalize_key(document_type)
        extractor = self._registry.get(enum_val)
        if extractor is not None:
            return extractor
        if self._default_extractor is not None:
            return self._default_extractor
        raise KeyError(f"No extractor registered for document type '{enum_val.value}' and no default provided.")

    def has_extractor(self, document_type: DocumentType | DocumentTypeEnum | str) -> bool:
        """Checks if an extractor is registered for document type."""
        enum_val = self._normalize_key(document_type)
        return enum_val in self._registry

    def _normalize_key(self, document_type: DocumentType | DocumentTypeEnum | str) -> DocumentTypeEnum:
        """Normalizes input key to DocumentTypeEnum."""
        if isinstance(document_type, DocumentType):
            return document_type.enum_value
        if isinstance(document_type, DocumentTypeEnum):
            return document_type
        if isinstance(document_type, str):
            return DocumentType.from_str(document_type).enum_value
        return DocumentTypeEnum.UNKNOWN
