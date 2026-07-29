"""Concrete document text extractor implementation."""

from app.domain.interfaces.text_extractor import TextExtractorInterface


class DefaultTextExtractor(TextExtractorInterface):
    """Default text extractor.

    Parses plain text documents directly via character decoding.
    Per Phase 3.2 requirements (No OCR / No AI engines), complex binary formats
    return structural placeholders until full parsers/OCR engines are wired in future phases.
    """

    async def extract_text(self, file_bytes: bytes, mime_type: str) -> str | None:
        """Extracts text content from raw bytes based on mime_type."""
        if not file_bytes:
            return ""

        normalized_mime = mime_type.lower().strip()

        if normalized_mime == "text/plain":
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

        # Non-text MIME types return a placeholder status in Phase 3.2 (infrastructure phase)
        return f"[Extracted raw text placeholder for {normalized_mime}]"
