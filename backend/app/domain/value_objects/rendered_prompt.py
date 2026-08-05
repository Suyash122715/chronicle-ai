"""RenderedPrompt domain value object."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RenderedPrompt:
    """Immutable domain value object encapsulating a rendered prompt template."""

    rendered_text: str
    schema: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = "v1"
    document_type: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Serializes rendered prompt for transport and logging."""
        return {
            "rendered_text": self.rendered_text,
            "schema": self.schema,
            "prompt_version": self.prompt_version,
            "document_type": self.document_type,
        }
