"""Health check response schema definition using Pydantic v2."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Pydantic v2 response model for GET /health endpoint."""

    status: str = "healthy"
