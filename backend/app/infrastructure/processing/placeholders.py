"""Placeholder extractor implementations for Phase 4.1."""

from datetime import datetime, timezone

from app.domain.entities.artifact import Artifact
from app.domain.interfaces.artifact_extractor import ArtifactExtractorInterface
from app.domain.value_objects.classification_result import ClassificationResult
from app.domain.value_objects.extraction_result import ExtractionResult


class BasePlaceholderExtractor(ArtifactExtractorInterface):
    """Base class for Phase 4.1 placeholder extractors."""

    extractor_name: str = "BasePlaceholderExtractor"

    async def extract(
        self,
        artifact: Artifact,
        classification_result: ClassificationResult,
    ) -> ExtractionResult:
        """Returns placeholder extraction result indicating feature is not implemented in Phase 4.1."""
        return ExtractionResult(
            artifact_id=artifact.id,
            extracted_data={},
            extractor_name=self.extractor_name,
            extracted_at=datetime.now(timezone.utc),
            is_placeholder=True,
            message="Not implemented in Phase 4.1",
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
