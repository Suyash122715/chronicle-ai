"""Provider-independent LLM service interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.value_objects.llm_response import LLMResponse


class LLMProviderInterface(ABC):
    """Provider-independent domain contract for LLM operations.

    Must NOT reference any vendor SDK (Gemini, OpenAI, Anthropic, etc.).
    """

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generates a structured LLM response conforming to requested JSON schema.

        Args:
            prompt: Formatted input prompt text.
            response_schema: Target JSON schema dictionary for structured output.
            prompt_version: Prompt version string.
            system_instruction: Optional system persona instruction text.
            temperature: Sampling temperature (defaults to 0.0 for deterministic extraction).
            **kwargs: Additional provider-agnostic parameters.

        Returns:
            An LLMResponse value object containing raw output, parsed JSON, token metrics, and metadata.
        """
        pass
