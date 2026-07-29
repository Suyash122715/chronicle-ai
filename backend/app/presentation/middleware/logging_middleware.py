"""HTTP request and execution time logging middleware."""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.logging.logger import get_logger

logger = get_logger("chronicle_ai.http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming HTTP request paths and response durations without logging secrets/tokens."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response: Response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        logger.info(
            "%s %s - Status %d - Completed in %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        return response
