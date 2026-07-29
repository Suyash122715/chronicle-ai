"""Text Extractor Interface definition.

Abstract interface for extracting raw text from binary document bytes.
Subsequent pipeline stages (OCR, AI summarization, etc.) can extend or replace
implementations of this interface without modifying domain or application logic.
"""

from abc import ABC, abstractmethod


class TextExtractorInterface(ABC):
    """Abstract interface defining document text extraction."""

    @abstractmethod
    async def extract_text(self, file_bytes: bytes, mime_type: str) -> str | None:
        """Extracts raw string text content from raw file bytes.

        Args:
            file_bytes: Binary contents of the document.
            mime_type: MIME type of the document (e.g. 'text/plain', 'application/pdf').

        Returns:
            str | None: Extracted text string or None if extraction is unsupported/empty.
        """
        pass
