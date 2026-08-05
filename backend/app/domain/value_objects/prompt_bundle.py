"""PromptBundle domain value object."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromptBundle:
    """Immutable domain value object holding raw prompt text, schema, and resolved version."""

    prompt_text: str
    output_schema: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        """Serializes prompt bundle for transport and inspection."""
        return {
            "prompt_text": self.prompt_text,
            "output_schema": self.output_schema,
            "prompt_version": self.prompt_version,
        }
