"""Rate limiting middleware for authentication endpoints."""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to rate limit authentication endpoints."""

    def __init__(self, app, enabled: bool = True):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.enabled = enabled and settings.auth_rate_limit_enabled
        # In-memory storage: {ip: [(timestamp, endpoint), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()

    def _cleanup_old_entries(self):
        """Remove entries older than 1 hour."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 3600  # 1 hour ago
        for ip in list(self.request_history.keys()):
            self.request_history[ip] = [
                (ts, endpoint)
                for ts, endpoint in self.request_history[ip]
                if ts > cutoff_time
            ]
            if not self.request_history[ip]:
                del self.request_history[ip]

        self.last_cleanup = current_time

    def _check_rate_limit(self, ip: str, endpoint: str) -> Tuple[bool, str]:
        """
        Check if request exceeds rate limit.

        Args:
            ip: Client IP address
            endpoint: Requested endpoint

        Returns:
            Tuple of (allowed, message)
        """
        if not self.enabled:
            return True, ""

        # Only rate limit auth endpoints
        if not endpoint.startswith("/api/auth"):
            return True, ""

        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Filter requests in the last minute and hour
        recent_requests = [
            ts for ts, ep in self.request_history[ip]
            if ts > minute_ago and ep.startswith("/api/auth")
        ]
        hourly_requests = [
            ts for ts, ep in self.request_history[ip]
            if ts > hour_ago and ep.startswith("/api/auth")
        ]

        # Check per-minute limit
        if len(recent_requests) >= settings.auth_rate_limit_per_minute:
            return False, f"Rate limit exceeded: {settings.auth_rate_limit_per_minute} requests per minute"

        # Check per-hour limit
        if len(hourly_requests) >= settings.auth_rate_limit_per_hour:
            return False, f"Rate limit exceeded: {settings.auth_rate_limit_per_hour} requests per hour"

        # Record this request
        self.request_history[ip].append((current_time, endpoint))

        return True, ""

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        # Cleanup old entries periodically
        self._cleanup_old_entries()

        # Get client IP
        ip_address = request.headers.get("X-Forwarded-For")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else "unknown"

        # Check rate limit
        allowed, message = self._check_rate_limit(ip_address, request.url.path)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response

