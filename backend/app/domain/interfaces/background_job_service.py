"""Background Job Service Interface definition.

Abstract interface decoupling background job dispatch from concrete execution mechanisms
(e.g., FastAPI BackgroundTasks, Celery, Redis Queue, Temporal).
"""

from abc import ABC, abstractmethod
from typing import Awaitable, Callable
from uuid import UUID


class BackgroundJobServiceInterface(ABC):
    """Abstract interface defining background job scheduling and execution."""

    @abstractmethod
    def enqueue_job(self, task: Callable[..., Awaitable[None]], *args, **kwargs) -> None:
        """Enqueues an asynchronous function for background execution.

        Args:
            task: Async callable function to execute in the background.
            *args: Positional arguments to pass to the task.
            **kwargs: Keyword arguments to pass to the task.
        """
        pass
