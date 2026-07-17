"""TestPilot AI — Request ID Middleware."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects a unique X-Request-ID into every request/response.

    If the incoming request already has an X-Request-ID header, that value
    is used. Otherwise, a new UUID4 is generated. The ID is propagated to
    the response headers and to the structlog context for log correlation.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Bind to structlog context for this request
        import structlog

        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Store on request state for use in route handlers
        request.state.request_id = request_id

        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request_id

        return response
