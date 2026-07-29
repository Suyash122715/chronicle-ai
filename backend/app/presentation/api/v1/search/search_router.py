"""Search router placeholder."""

from fastapi import APIRouter

search_router = APIRouter(prefix="/search", tags=["Search"])

# TODO: Add Phase 7 Search Endpoints:
# - GET /search (Keyword search)
# - POST /search/semantic (Vector semantic search)
# - POST /search/hybrid (Combined search)
