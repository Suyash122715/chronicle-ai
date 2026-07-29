"""Aggregated API v1 router definition."""

from fastapi import APIRouter
from app.presentation.api.v1.health.health_router import health_router
from app.presentation.api.v1.authentication.auth_router import auth_router

api_v1_router = APIRouter()

# Mount active routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)

# TODO: Mount Phase 3+ feature routers when implemented:
# - api_v1_router.include_router(artifact_router)
# - api_v1_router.include_router(search_router)
# - api_v1_router.include_router(timeline_router)
# - api_v1_router.include_router(graph_router)
# - api_v1_router.include_router(job_router)
# - api_v1_router.include_router(user_router)
