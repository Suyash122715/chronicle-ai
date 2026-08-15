"""Artifact management router containing upload, list, get, and delete endpoints."""

from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status

from app.application.artifacts.delete.delete_artifact_use_case import DeleteArtifactUseCase
from app.application.artifacts.get.get_artifact_use_case import GetArtifactUseCase
from app.application.artifacts.get_extraction.get_extraction_use_case import GetExtractionUseCase
from app.application.artifacts.list.list_artifacts_use_case import ListArtifactsUseCase
from app.application.artifacts.upload.upload_artifact_use_case import UploadArtifactUseCase
from app.dependencies import (
    get_artifact_repository,
    get_current_user,
    get_delete_artifact_use_case,
    get_get_artifact_use_case,
    get_get_extraction_use_case,
    get_list_artifacts_use_case,
    get_process_artifact_use_case,
    get_storage_service,
)
from app.domain.entities.user import User
from app.infrastructure.jobs.fastapi_background_job_service import FastAPIBackgroundJobService
from app.presentation.schemas.artifact_response import ArtifactResponse, UploadArtifactResponse
from app.presentation.schemas.extraction_response import ExtractionResponse

artifact_router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@artifact_router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadArtifactResponse,
    summary="Upload Artifact",
    description="Uploads a new document/file artifact and enqueues background processing.",
)
async def upload_artifact(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    artifact_repository=Depends(get_artifact_repository),
    storage_service=Depends(get_storage_service),
    process_use_case=Depends(get_process_artifact_use_case),
) -> UploadArtifactResponse:
    """Handles POST /api/v1/artifacts/upload.

    Validates file size and MIME type, saves binary content to local storage,
    persists metadata with status=PENDING, enqueues async background processing,
    and returns HTTP 201 Created immediately.
    """
    file_bytes = await file.read()
    filename = file.filename or "unnamed_file"
    mime_type = file.content_type or "application/octet-stream"

    job_service = FastAPIBackgroundJobService(background_tasks=background_tasks)
    use_case = UploadArtifactUseCase(
        artifact_repository=artifact_repository,
        storage_service=storage_service,
        background_job_service=job_service,
        process_task=process_use_case.execute,
    )

    artifact = await use_case.execute(
        user_id=current_user.id,
        filename=filename,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    return UploadArtifactResponse(
        artifact=ArtifactResponse.model_validate(artifact),
        message="Artifact uploaded successfully.",
    )


@artifact_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ArtifactResponse],
    summary="List User Artifacts",
    description="Retrieves all uploaded artifacts owned by the currently authenticated user.",
)
async def list_artifacts(
    current_user: User = Depends(get_current_user),
    use_case: ListArtifactsUseCase = Depends(get_list_artifacts_use_case),
) -> list[ArtifactResponse]:
    """Handles GET /api/v1/artifacts."""
    artifacts = await use_case.execute(user_id=current_user.id)
    return [ArtifactResponse.model_validate(artifact) for artifact in artifacts]


@artifact_router.get(
    "/{artifact_id}",
    status_code=status.HTTP_200_OK,
    response_model=ArtifactResponse,
    summary="Get Artifact Details",
    description="Retrieves metadata for a specific artifact owned by the authenticated user.",
)
async def get_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetArtifactUseCase = Depends(get_get_artifact_use_case),
) -> ArtifactResponse:
    """Handles GET /api/v1/artifacts/{artifact_id}."""
    artifact = await use_case.execute(user_id=current_user.id, artifact_id=artifact_id)
    return ArtifactResponse.model_validate(artifact)


@artifact_router.get(
    "/{artifact_id}/extraction",
    status_code=status.HTTP_200_OK,
    response_model=ExtractionResponse,
    summary="Get Artifact Extraction Result",
    description="Retrieves the extraction result for a specific artifact owned by the authenticated user.",
)
async def get_artifact_extraction(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetExtractionUseCase = Depends(get_get_extraction_use_case),
) -> ExtractionResponse:
    """Handles GET /api/v1/artifacts/{artifact_id}/extraction."""
    extraction = await use_case.execute(user_id=current_user.id, artifact_id=artifact_id)
    return ExtractionResponse.from_domain(extraction)



@artifact_router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Artifact",
    description="Deletes an artifact record and removes its physical file from storage.",
)
async def delete_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: DeleteArtifactUseCase = Depends(get_delete_artifact_use_case),
) -> None:
    """Handles DELETE /api/v1/artifacts/{artifact_id}."""
    await use_case.execute(user_id=current_user.id, artifact_id=artifact_id)
