"""Deterministic document classifier implementation."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from app.domain.interfaces.document_classifier import DocumentClassifierInterface
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.provenance import Provenance

DETERMINISTIC_CLASSIFIER_VERSION: str = "deterministic-1.0"


class DeterministicDocumentClassifier(DocumentClassifierInterface):
    """Rule-based, deterministic document classifier implementation.

    Strictly evaluates artifacts based on deterministic rule priority:
    1. Filename rules (Highest Priority) -> HIGH confidence
    2. Extension rules -> HIGH confidence if Extension + MIME agree, else MEDIUM
    3. MIME rules -> MEDIUM confidence
    4. Metadata rules -> LOW confidence
    5. Unknown fallback -> LOW confidence
    """

    def __init__(self, classifier_version: str = DETERMINISTIC_CLASSIFIER_VERSION) -> None:
        self._classifier_version = classifier_version

    async def classify(
        self,
        artifact_id: UUID,
        filename: str,
        mime_type: str,
        file_size: int,
        metadata: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """Classifies an artifact using strict deterministic rule ordering."""
        now = datetime.now(timezone.utc)
        safe_metadata = metadata or {}
        lowercased_filename = filename.lower()
        file_stem = Path(filename).stem.lower()
        extension = Path(filename).suffix.lower()
        lowercased_mime = mime_type.lower()

        # 1. Filename Rules (Highest Priority) -> HIGH Confidence
        filename_match = self._match_filename_rules(lowercased_filename, file_stem)
        if filename_match:
            doc_type, pattern = filename_match
            provenance = Provenance(
                artifact_id=artifact_id,
                evidence_snippet=f"Matched filename pattern '{pattern}' in '{filename}'",
                evidence_location="filename",
                confidence=ConfidenceLevel.HIGH.value,
                extraction_version=self._classifier_version,
            )
            return ClassificationResult(
                document_type=doc_type,
                confidence_level=ConfidenceLevel.HIGH,
                classifier_version=self._classifier_version,
                classified_at=now,
                provenance=provenance,
            )

        # 2. Extension Rules (Second Priority)
        # Agreement between Extension and MIME type gives HIGH confidence, extension alone gives MEDIUM.
        extension_match = self._match_extension_rules(extension, lowercased_mime)
        if extension_match:
            doc_type, confidence, detail = extension_match
            provenance = Provenance(
                artifact_id=artifact_id,
                evidence_snippet=detail,
                evidence_location="extension",
                confidence=confidence.value,
                extraction_version=self._classifier_version,
            )
            return ClassificationResult(
                document_type=doc_type,
                confidence_level=confidence,
                classifier_version=self._classifier_version,
                classified_at=now,
                provenance=provenance,
            )

        # 3. MIME Rules (Third Priority)
        mime_match = self._match_mime_rules(lowercased_mime)
        if mime_match:
            doc_type, pattern = mime_match
            provenance = Provenance(
                artifact_id=artifact_id,
                evidence_snippet=f"Matched MIME type '{pattern}'",
                evidence_location="mime_type",
                confidence=ConfidenceLevel.MEDIUM.value,
                extraction_version=self._classifier_version,
            )
            return ClassificationResult(
                document_type=doc_type,
                confidence_level=ConfidenceLevel.MEDIUM,
                classifier_version=self._classifier_version,
                classified_at=now,
                provenance=provenance,
            )

        # 4. Metadata Rules (Fourth Priority) -> LOW Confidence
        metadata_match = self._match_metadata_rules(safe_metadata)
        if metadata_match:
            doc_type, detail = metadata_match
            provenance = Provenance(
                artifact_id=artifact_id,
                evidence_snippet=detail,
                evidence_location="metadata",
                confidence=ConfidenceLevel.LOW.value,
                extraction_version=self._classifier_version,
            )
            return ClassificationResult(
                document_type=doc_type,
                confidence_level=ConfidenceLevel.LOW,
                classifier_version=self._classifier_version,
                classified_at=now,
                provenance=provenance,
            )

        # 5. Unknown Fallback -> LOW Confidence
        provenance = Provenance(
            artifact_id=artifact_id,
            evidence_snippet="No deterministic rules matched; falling back to Unknown",
            evidence_location="fallback",
            confidence=ConfidenceLevel.LOW.value,
            extraction_version=self._classifier_version,
        )
        return ClassificationResult(
            document_type=DocumentType.unknown(),
            confidence_level=ConfidenceLevel.LOW,
            classifier_version=self._classifier_version,
            classified_at=now,
            provenance=provenance,
        )

    def _match_filename_rules(self, full_filename: str, stem: str) -> tuple[DocumentType, str] | None:
        """Matches filename against deterministic keyword patterns."""
        filename_patterns: list[tuple[list[str], DocumentType]] = [
            (["resume", "cv", "curriculum_vitae", "curriculumvitae"], DocumentType.resume()),
            (["certificate", "cert", "degree", "diploma", "completion"], DocumentType.certificate()),
            (["marksheet", "transcript", "grade_sheet", "gradesheet", "grade"], DocumentType.marksheet()),
            (["internship", "offer_letter", "offerletter", "experience_letter", "relieving_letter"], DocumentType.internship_letter()),
            (["project_report", "project_doc", "synopsis", "capstone_report"], DocumentType.project_report()),
            (["portfolio"], DocumentType.portfolio()),
            (["github", "repository", "repo"], DocumentType.github_repository()),
        ]

        for keywords, doc_type in filename_patterns:
            for kw in keywords:
                if kw in stem or kw in full_filename:
                    return doc_type, kw
        return None

    def _match_extension_rules(self, extension: str, mime_type: str) -> tuple[DocumentType, ConfidenceLevel, str] | None:
        """Matches extension rules with MIME agreement check."""
        if extension in (".githubrepo", ".gitrepo"):
            return DocumentType.github_repository(), ConfidenceLevel.MEDIUM, f"Matched dedicated extension '{extension}'"
        if extension in (".portfolio", ".port"):
            return DocumentType.portfolio(), ConfidenceLevel.MEDIUM, f"Matched dedicated extension '{extension}'"

        return None

    def _match_mime_rules(self, mime_type: str) -> tuple[DocumentType, str] | None:
        """Matches MIME type rules."""
        if mime_type == "application/vnd.github+json":
            return DocumentType.github_repository(), "application/vnd.github+json"
        return None

    def _match_metadata_rules(self, metadata: dict[str, Any]) -> tuple[DocumentType, str] | None:
        """Matches metadata attributes."""
        source = str(metadata.get("source", "")).strip().lower()
        if source == "github" or "github_url" in metadata:
            return DocumentType.github_repository(), "Matched GitHub source in metadata"
        if source == "portfolio":
            return DocumentType.portfolio(), "Matched Portfolio source in metadata"
        return None
