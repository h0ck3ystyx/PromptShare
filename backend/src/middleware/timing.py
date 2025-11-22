"""Timing middleware for FastAPI application."""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request timing information."""

    async def dispatch(self, request: Request, call_next):
        """Add timing header to response."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

