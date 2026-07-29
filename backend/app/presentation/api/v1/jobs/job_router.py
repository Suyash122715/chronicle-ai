"""Background Processing Job router placeholder."""

from fastapi import APIRouter

job_router = APIRouter(prefix="/jobs", tags=["Jobs"])

# TODO: Add Job Status Endpoints:
# - GET /jobs/{job_id} (Check async upload job status)
