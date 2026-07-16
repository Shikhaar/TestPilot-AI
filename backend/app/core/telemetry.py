"""
TestPilot AI — OpenTelemetry Instrumentation.

Configures distributed tracing and metrics export via OpenTelemetry.
Instruments FastAPI, SQLAlchemy, Redis, and Celery automatically.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def configure_telemetry(app: object | None = None) -> TracerProvider:
    """Configure OpenTelemetry tracing.

    Sets up the OTLP exporter for production and console exporter for dev.
    Auto-instruments FastAPI, SQLAlchemy, Redis, and Celery.

    Args:
        app: Optional FastAPI application instance for auto-instrumentation.

    Returns:
        The configured TracerProvider.
    """
    settings = get_settings()

    # Resource metadata attached to all spans
    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: settings.otel_service_name,
            ResourceAttributes.SERVICE_VERSION: settings.app_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.otel_environment,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.is_production:
        # Export to OTLP collector in production
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(
            "OpenTelemetry configured with OTLP exporter",
            endpoint=settings.otel_exporter_otlp_endpoint,
        )
    else:
        # Console exporter for development (prints spans to stdout)
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry configured with console exporter")

    trace.set_tracer_provider(provider)

    # Auto-instrument libraries
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]

    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    CeleryInstrumentor().instrument()

    logger.info("OpenTelemetry instrumentation enabled")
    return provider


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given module.

    Args:
        name: The tracer name, typically __name__.

    Returns:
        An OpenTelemetry Tracer instance.
    """
    return trace.get_tracer(name)
