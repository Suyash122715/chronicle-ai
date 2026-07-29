"""Integration tests for GET /health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_healthy_status(async_client: AsyncClient) -> None:
    """Verifies that GET /health returns HTTP 200 and {'status': 'healthy'} payload."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_check_v1_returns_healthy_status(async_client: AsyncClient) -> None:
    """Verifies that GET /api/v1/health returns HTTP 200 and {'status': 'healthy'} payload."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
