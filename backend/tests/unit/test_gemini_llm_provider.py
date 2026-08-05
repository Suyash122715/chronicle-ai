"""Unit tests for GeminiLLMProvider using mocks (no live API calls)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.interfaces.llm_provider import LLMProviderInterface
from app.domain.value_objects.llm_response import LLMResponse
from app.infrastructure.ai.gemini_provider import GeminiLLMProvider, GeminiProviderError


# ---------------------------------------------------------------------------
# Helpers & Mocks
# ---------------------------------------------------------------------------

def make_mock_sdk_response(
    text: str = '{"name": "John Doe"}',
    finish_reason_name: str = "STOP",
    prompt_tokens: int = 50,
    completion_tokens: int = 20,
    total_tokens: int = 70,
) -> MagicMock:
    """Helper to create a mock google.generativeai response object."""
    mock_resp = MagicMock()
    mock_resp.text = text

    candidate = MagicMock()
    candidate.finish_reason.name = finish_reason_name
    mock_resp.candidates = [candidate]

    usage = MagicMock()
    usage.prompt_token_count = prompt_tokens
    usage.candidates_token_count = completion_tokens
    usage.total_token_count = total_tokens
    mock_resp.usage_metadata = usage

    return mock_resp


# ---------------------------------------------------------------------------
# Contract & Unit Tests
# ---------------------------------------------------------------------------

def test_gemini_provider_implements_interface() -> None:
    """Contract test: verifies GeminiLLMProvider is a subclass of LLMProviderInterface."""
    assert issubclass(GeminiLLMProvider, LLMProviderInterface)


def test_missing_api_key_raises_value_error() -> None:
    """Verifies that empty API key raises ValueError during initialization."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY must not be empty"):
        GeminiLLMProvider(api_key="")


@pytest.mark.asyncio
@patch("app.infrastructure.ai.gemini_provider.genai")
async def test_successful_structured_generation(mock_genai: MagicMock) -> None:
    """Verifies successful call converts Gemini response into standard LLMResponse."""
    mock_model = MagicMock()
    mock_sdk_resp = make_mock_sdk_response(
        text='{"skill": "Python"}',
        finish_reason_name="STOP",
        prompt_tokens=40,
        completion_tokens=15,
        total_tokens=55,
    )
    mock_model.generate_content_async = AsyncMock(return_value=mock_sdk_resp)
    mock_genai.GenerativeModel.return_value = mock_model

    provider = GeminiLLMProvider(
        api_key="test-api-key",
        model="gemini-1.5-flash",
        timeout_seconds=30,
    )

    response = await provider.generate_structured(
        prompt="Extract skill from text",
        response_schema={"type": "object"},
        prompt_version="v1",
    )

    assert isinstance(response, LLMResponse)
    assert response.provider == "gemini"
    assert response.model == "gemini-1.5-flash"
    assert response.parsed_json == {"skill": "Python"}
    assert response.raw_response == '{"skill": "Python"}'
    assert response.finish_reason == "STOP"
    assert response.prompt_version == "v1"
    assert response.token_usage == {
        "prompt_tokens": 40,
        "completion_tokens": 15,
        "total_tokens": 55,
    }
    assert response.latency >= 0.0


@pytest.mark.asyncio
@patch("app.infrastructure.ai.gemini_provider.genai")
async def test_sdk_exception_wrapped_in_gemini_provider_error(mock_genai: MagicMock) -> None:
    """Verifies SDK exceptions are caught and wrapped in GeminiProviderError without leaking SDK types."""
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(side_effect=RuntimeError("SDK Internal Error"))
    mock_genai.GenerativeModel.return_value = mock_model

    provider = GeminiLLMProvider(api_key="test-key")

    with pytest.raises(GeminiProviderError, match="Gemini API call failed: SDK Internal Error"):
        await provider.generate_structured(
            prompt="Test prompt",
            response_schema={},
        )


@pytest.mark.asyncio
@patch("app.infrastructure.ai.gemini_provider.genai")
async def test_invalid_json_handled_gracefully(mock_genai: MagicMock) -> None:
    """Verifies non-JSON response sets parsed_json to None without crashing."""
    mock_model = MagicMock()
    mock_sdk_resp = make_mock_sdk_response(text="Plain text output, not JSON")
    mock_model.generate_content_async = AsyncMock(return_value=mock_sdk_resp)
    mock_genai.GenerativeModel.return_value = mock_model

    provider = GeminiLLMProvider(api_key="test-key")

    response = await provider.generate_structured(
        prompt="Test prompt",
        response_schema={},
    )

    assert response.parsed_json is None
    assert response.raw_response == "Plain text output, not JSON"


@pytest.mark.asyncio
@patch("app.infrastructure.ai.gemini_provider.genai")
async def test_system_instruction_creates_configured_model(mock_genai: MagicMock) -> None:
    """Verifies system_instruction creates a fresh GenerativeModel instance with system_instruction."""
    mock_base_model = MagicMock()
    mock_system_model = MagicMock()

    mock_sdk_resp = make_mock_sdk_response()
    mock_system_model.generate_content_async = AsyncMock(return_value=mock_sdk_resp)

    # First call in init returns mock_base_model, second call in method returns mock_system_model
    mock_genai.GenerativeModel.side_effect = [mock_base_model, mock_system_model]

    provider = GeminiLLMProvider(api_key="test-key")

    await provider.generate_structured(
        prompt="Test prompt",
        response_schema={},
        system_instruction="You are an expert resume parser.",
    )

    # Check system instruction was passed to GenerativeModel constructor
    mock_genai.GenerativeModel.assert_called_with(
        model_name="gemini-1.5-flash",
        system_instruction="You are an expert resume parser.",
    )
