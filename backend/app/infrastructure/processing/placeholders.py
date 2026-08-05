"""Placeholder extractor implementations for Phase 4.1 / Phase 4.2."""

from datetime import datetime, timezone

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.value_objects.classification_result import ClassificationResult
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus


class BasePlaceholderExtractor(ArtifactExtractorInterface):
    """Base class for placeholder extractors."""

    extractor_name: str = "BasePlaceholderExtractor"

    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        """Returns placeholder canonical extraction result."""
        now = datetime.now(timezone.utc)
        return ExtractionResult(
            artifact_id=artifact.id,
            document_type=classification_result.document_type,
            structured_data={},
            provenance={},
            warnings=["Placeholder extractor; not implemented in Phase 4.1"],
            confidence=classification_result.confidence_level,
            extractor_version=self.extractor_name,
            prompt_version="v0",
            llm_metadata={
                "is_placeholder": True,
                "message": "Not implemented in Phase 4.1",
            },
            started_at=now,
            completed_at=now,
            status=ExtractionStatus.SUCCESS,
        )


class ResumeExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Resume artifacts."""

    extractor_name: str = "ResumeExtractor"


class CertificateExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Certificate artifacts."""

    extractor_name: str = "CertificateExtractor"


class MarksheetExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Marksheet artifacts."""

    extractor_name: str = "MarksheetExtractor"


class InternshipLetterExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Internship Letter artifacts."""

    extractor_name: str = "InternshipLetterExtractor"


class ProjectReportExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Project Report artifacts."""

    extractor_name: str = "ProjectReportExtractor"


class PortfolioExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Portfolio artifacts."""

    extractor_name: str = "PortfolioExtractor"


class GitHubRepositoryExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for GitHub Repository artifacts."""

    extractor_name: str = "GitHubRepositoryExtractor"


class UnknownExtractor(BasePlaceholderExtractor):
    """Placeholder extractor for Unknown artifacts."""

    extractor_name: str = "UnknownExtractor"
