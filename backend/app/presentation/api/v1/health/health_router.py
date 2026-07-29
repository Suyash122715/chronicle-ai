"""Health check endpoint router."""

from fastapi import APIRouter, status
from app.presentation.schemas.health_response import HealthResponse

health_router = APIRouter(tags=["Health"])


@health_router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns liveness status of the Chronicle AI backend service.",
)
async def check_health() -> HealthResponse:
    """Returns status healthy if application is running."""
    return HealthResponse(status="healthy")
