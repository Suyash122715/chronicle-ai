"""Unit tests for LLMResponse domain value object."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.value_objects import LLMResponse


def test_llm_response_creation_and_token_usage() -> None:
    response = LLMResponse(
        raw_response='{"name": "Alice"}',
        parsed_json={"name": "Alice"},
        token_usage={
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        latency=0.42,
        provider="mock_provider",
        model="mock_model_v1",
        finish_reason="STOP",
        prompt_version="v1",
        metadata={"estimated_cost_usd": 0.0002, "rate_limit_remaining": 99},
    )

    assert response.raw_response == '{"name": "Alice"}'
    assert response.parsed_json == {"name": "Alice"}
    assert response.token_usage["prompt_tokens"] == 100
    assert response.token_usage["completion_tokens"] == 50
    assert response.token_usage["total_tokens"] == 150
    assert response.latency == 0.42
    assert response.provider == "mock_provider"
    assert response.model == "mock_model_v1"
    assert response.metadata["estimated_cost_usd"] == 0.0002

    serialized = response.to_dict()
    assert serialized["provider"] == "mock_provider"
    assert serialized["token_usage"]["total_tokens"] == 150
    assert serialized["metadata"]["estimated_cost_usd"] == 0.0002


def test_llm_response_immutability() -> None:
    response = LLMResponse(raw_response="test")
    with pytest.raises(FrozenInstanceError):
        response.provider = "gemini"  # type: ignore[misc]
