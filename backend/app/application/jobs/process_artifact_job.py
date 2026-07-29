"""Process Artifact Job wrapper."""

from uuid import UUID

from app.application.artifacts.process.process_artifact_use_case import ProcessArtifactUseCase


class ProcessArtifactJob:
    """Orchestrates asynchronous processing of uploaded artifacts."""

    def __init__(self, process_artifact_use_case: ProcessArtifactUseCase) -> None:
        self._process_artifact_use_case = process_artifact_use_case

    async def execute(self, artifact_id: UUID) -> None:
        """Executes background artifact processing."""
        await self._process_artifact_use_case.execute(artifact_id)
