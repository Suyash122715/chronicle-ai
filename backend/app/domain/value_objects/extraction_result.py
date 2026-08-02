"""ExtractionResult domain value object placeholder."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ExtractionResult:
    """Immutable domain value object representing the result of artifact extraction (placeholder for Phase 4.1)."""

    artifact_id: UUID
    extracted_data: dict[str, Any] = field(default_factory=dict)
    extractor_name: str = "placeholder_extractor"
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_placeholder: bool = True
    message: str = "Not implemented in Phase 4.1"
