"""TestPilot AI — Rate Limiting Middleware."""

from __future__ import annotations

import time
from collections import defaultdict

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding window rate limiter.

    Limits requests per IP address per minute. For production use,
    this should be replaced with a Redis-based distributed rate limiter.

    The /health and /metrics endpoints are exempt from rate limiting.
    """

    EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app: ASGIApp, **kwargs: Any) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        # {ip: [(timestamp, count)]}
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._limit = settings.rate_limit_requests_per_minute
        self._window = 60.0  # seconds

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)  # type: ignore[operator]

        client_ip = self._get_client_ip(request)
        now = time.monotonic()

        # Sliding window: remove timestamps older than window
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if now - ts < self._window
        ]

        if len(self._requests[client_ip]) >= self._limit:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
                limit=self._limit,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self._limit} requests per minute",
                    "retry_after": int(self._window),
                },
                headers={"Retry-After": str(int(self._window))},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)  # type: ignore[operator]

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the real client IP, considering proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
