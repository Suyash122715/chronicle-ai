"""LLMResponse domain value object representation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    """Provider-independent immutable domain value object encapsulating LLM execution output."""

    raw_response: str
    parsed_json: dict[str, Any] | None = None
    token_usage: dict[str, int] = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )
    latency: float = 0.0
    provider: str = "unknown"
    model: str = "unknown"
    finish_reason: str = "STOP"
    prompt_version: str = "v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializes LLM response for transport, logging, and observability."""
        return {
            "raw_response": self.raw_response,
            "parsed_json": self.parsed_json,
            "token_usage": self.token_usage,
            "latency": self.latency,
            "provider": self.provider,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "prompt_version": self.prompt_version,
            "metadata": self.metadata,
        }
