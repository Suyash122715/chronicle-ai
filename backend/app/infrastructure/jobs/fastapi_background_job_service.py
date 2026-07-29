"""FastAPI BackgroundTasks implementation of BackgroundJobServiceInterface."""

import asyncio
from typing import Awaitable, Callable

from fastapi import BackgroundTasks

from app.domain.interfaces.background_job_service import BackgroundJobServiceInterface
from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.jobs")


class FastAPIBackgroundJobService(BackgroundJobServiceInterface):
    """Concrete job runner using FastAPI BackgroundTasks or asyncio event loop."""

    def __init__(self, background_tasks: BackgroundTasks | None = None) -> None:
        self._background_tasks = background_tasks

    def enqueue_job(self, task: Callable[..., Awaitable[None]], *args, **kwargs) -> None:
        """Enqueues an async task for non-blocking background execution."""
        if self._background_tasks is not None:
            self._background_tasks.add_task(task, *args, **kwargs)
        else:
            # Fallback for out-of-request context execution (e.g. background event loop execution)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._run_async(task, *args, **kwargs))
            else:
                loop.run_until_complete(task(*args, **kwargs))

    async def _run_async(self, task: Callable[..., Awaitable[None]], *args, **kwargs) -> None:
        try:
            await task(*args, **kwargs)
        except Exception as exc:
            logger.error("Background task failed execution: %s", str(exc), exc_info=True)
