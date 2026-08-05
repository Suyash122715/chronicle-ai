"""GeminiLLMProvider — infrastructure adapter for Google Gemini."""

import json
import time
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.value_objects.llm_response import LLMResponse


class GeminiProviderError(Exception):
    """Provider-independent wrapper for Gemini SDK errors."""


class GeminiLLMProvider(LLMProviderInterface):
    """Infrastructure adapter converting Gemini SDK calls into provider-independent LLMResponse.

    Responsibilities ONLY:
    - Accept a rendered prompt and JSON schema.
    - Call Gemini via the SDK.
    - Convert the SDK response into an LLMResponse value object.

    No extraction logic.
    No prompt loading or rendering.
    No business rules.
    """

    PROVIDER_NAME: str = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY must not be empty.")
        self._model_name = model
        self._timeout_seconds = timeout_seconds

        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model_name=model)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        prompt_version: str = "v1",
        system_instruction: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Sends the rendered prompt to Gemini and returns a provider-independent LLMResponse.

        Args:
            prompt: Fully rendered prompt text.
            response_schema: JSON schema dict the response must conform to.
            prompt_version: Version string of the prompt used.
            system_instruction: Optional system persona instruction.
            temperature: Sampling temperature (0.0 = deterministic).
            **kwargs: Additional SDK parameters (ignored safely for forward compatibility).

        Returns:
            An LLMResponse value object.

        Raises:
            GeminiProviderError: For all Gemini SDK errors, converted to a provider-independent form.
        """
        start = time.monotonic()

        try:
            client = self._client
            if system_instruction:
                # Gemini supports system_instruction at model level; create one-off instance.
                client = genai.GenerativeModel(
                    model_name=self._model_name,
                    system_instruction=system_instruction,
                )

            generation_config = GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
            )

            raw_response = await client.generate_content_async(
                contents=prompt,
                generation_config=generation_config,
                request_options={"timeout": self._timeout_seconds},
            )

        except Exception as exc:
            raise GeminiProviderError(f"Gemini API call failed: {exc}") from exc

        latency = time.monotonic() - start

        return self._convert_response(raw_response, prompt_version=prompt_version, latency=latency)

    def _convert_response(
        self,
        raw_response: Any,
        prompt_version: str,
        latency: float,
    ) -> LLMResponse:
        """Converts the raw Gemini SDK response into an LLMResponse value object."""
        raw_text = ""
        parsed_json: dict[str, Any] | None = None
        finish_reason = "UNKNOWN"
        token_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            raw_text = raw_response.text
        except (AttributeError, ValueError):
            raw_text = ""

        if raw_text:
            try:
                parsed_json = json.loads(raw_text)
            except json.JSONDecodeError:
                parsed_json = None

        try:
            candidates = raw_response.candidates
            if candidates:
                finish_reason = str(candidates[0].finish_reason.name)
        except AttributeError:
            finish_reason = "UNKNOWN"

        try:
            usage = raw_response.usage_metadata
            token_usage = {
                "prompt_tokens": usage.prompt_token_count or 0,
                "completion_tokens": usage.candidates_token_count or 0,
                "total_tokens": usage.total_token_count or 0,
            }
        except AttributeError:
            pass

        return LLMResponse(
            raw_response=raw_text,
            parsed_json=parsed_json,
            token_usage=token_usage,
            latency=round(latency, 4),
            provider=self.PROVIDER_NAME,
            model=self._model_name,
            finish_reason=finish_reason,
            prompt_version=prompt_version,
            metadata={},
        )
