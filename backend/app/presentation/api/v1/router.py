"""Aggregated API v1 router definition."""

from fastapi import APIRouter

from app.presentation.api.v1.artifacts.artifact_router import artifact_router
from app.presentation.api.v1.authentication.auth_router import auth_router
from app.presentation.api.v1.graph.graph_router import graph_router
from app.presentation.api.v1.health.health_router import health_router
from app.presentation.api.v1.users.user_router import user_router

api_v1_router = APIRouter()

# Mount active routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(artifact_router)
api_v1_router.include_router(graph_router)

# TODO: Mount Phase 3.2+ feature routers when implemented:
# - api_v1_router.include_router(search_router)
# - api_v1_router.include_router(timeline_router)
# - api_v1_router.include_router(job_router)

