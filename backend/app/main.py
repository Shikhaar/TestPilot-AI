"""
TestPilot AI — FastAPI Application Entry Point.

Configures:
- CORS, middleware, and compression
- OpenTelemetry instrumentation
- Prometheus metrics endpoint
- Structured logging
- Global exception handlers
- API router with versioning
- WebSocket support for real-time streaming
- Health check endpoint
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.telemetry import configure_telemetry

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

# ==============================================================================
# Prometheus Metrics
# ==============================================================================

REQUEST_COUNT = Counter(
    "testpilot_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_DURATION = Histogram(
    "testpilot_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
PR_ANALYSIS_COUNT = Counter(
    "testpilot_pr_analyses_total",
    "Total PR analyses triggered",
    ["status"],
)


# ==============================================================================
# Application Lifespan
# ==============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle manager.

    Startup:
    - Configure OpenTelemetry
    - Initialize Qdrant collections
    - Warm up embedding model

    Shutdown:
    - Close database connections
    - Flush telemetry spans
    """
    logger.info(
        "Starting TestPilot AI",
        version=settings.app_version,
        environment=settings.app_env,
    )

    # Configure OpenTelemetry (instruments the app automatically)
    configure_telemetry(app)

    # Initialize Qdrant collections
    await _initialize_qdrant()

    logger.info("TestPilot AI started successfully")
    yield

    # Shutdown
    logger.info("Shutting down TestPilot AI")


# ==============================================================================
# Application Factory
# ==============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        description="AI-Powered Regression Testing Platform for Modern Software Engineering Teams",
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # --------------------------------------------------------------------------
    # Middleware
    # --------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Import and add custom middleware
    from app.middleware.rate_limit import RateLimitMiddleware
    from app.middleware.request_id import RequestIDMiddleware

    app.add_middleware(RequestIDMiddleware)
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)

    # --------------------------------------------------------------------------
    # Request timing middleware
    # --------------------------------------------------------------------------
    @app.middleware("http")
    async def track_request_metrics(request: Request, call_next: object) -> Response:
        """Track request duration and count via Prometheus."""
        start = time.monotonic()
        import structlog

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request.headers.get("X-Request-ID", ""),
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)  # type: ignore[operator]

        duration = time.monotonic() - start
        endpoint = request.url.path
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_DURATION.labels(request.method, endpoint).observe(duration)

        logger.info(
            "HTTP request",
            method=request.method,
            path=endpoint,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 1),
        )
        return response

    # --------------------------------------------------------------------------
    # Exception handlers
    # --------------------------------------------------------------------------
    from fastapi.exceptions import RequestValidationError

    from app.schemas.common import ErrorResponse

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Request validation error", errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Validation Error",
                detail=str(exc.errors()),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred." if settings.is_production else str(exc),
            ).model_dump(),
        )

    # --------------------------------------------------------------------------
    # Health check
    # --------------------------------------------------------------------------
    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, object]:
        """Service health check endpoint."""
        from app.schemas.common import HealthResponse

        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            environment=settings.app_env,
            services=await _check_services(),
        ).model_dump()

    # --------------------------------------------------------------------------
    # Prometheus metrics endpoint
    # --------------------------------------------------------------------------
    @app.get("/metrics", tags=["System"])
    async def prometheus_metrics() -> Response:
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    # --------------------------------------------------------------------------
    # API Router
    # --------------------------------------------------------------------------
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    # --------------------------------------------------------------------------
    # WebSocket endpoints
    # --------------------------------------------------------------------------
    from app.api.websocket import ws_router

    app.include_router(ws_router, prefix="/ws")

    return app


# ==============================================================================
# Helpers
# ==============================================================================


async def _initialize_qdrant() -> None:
    """Initialize Qdrant collections if they don't exist."""
    try:
        from app.utils.qdrant_client import get_qdrant_client, initialize_collections

        qdrant = get_qdrant_client()
        await initialize_collections(qdrant)
        logger.info("Qdrant collections initialized")
    except Exception as e:
        logger.warning("Qdrant initialization failed (non-fatal)", error=str(e))


async def _check_services() -> dict[str, str]:
    """Check health of dependent services."""
    services: dict[str, str] = {}

    # PostgreSQL
    try:
        from app.database.session import engine

        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        services["postgres"] = "healthy"
    except Exception:
        services["postgres"] = "unhealthy"

    # Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        services["redis"] = "healthy"
    except Exception:
        services["redis"] = "unhealthy"

    # Qdrant
    try:
        from app.utils.qdrant_client import get_qdrant_client

        qdrant = get_qdrant_client()
        qdrant.get_collections()
        services["qdrant"] = "healthy"
    except Exception:
        services["qdrant"] = "unhealthy"

    return services


# ==============================================================================
# Application Instance
# ==============================================================================

app = create_app()
