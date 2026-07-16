"""
TestPilot AI — Celery Application.

Configures the Celery distributed task queue using Redis as broker and
result backend. Handles PR analysis pipeline and repository indexing
as background tasks.
"""

from __future__ import annotations

from celery import Celery
from celery.signals import setup_logging, worker_ready
from kombu import Queue

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)
settings = get_settings()

# ==============================================================================
# Celery Application
# ==============================================================================

celery_app = Celery(
    "testpilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.pr_pipeline",
        "app.tasks.indexing",
        "app.tasks.notifications",
    ],
)

# ==============================================================================
# Configuration
# ==============================================================================

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing / queues
    task_queues=[
        Queue("pr_pipeline", routing_key="pr_pipeline"),
        Queue("indexing", routing_key="indexing"),
        Queue("notifications", routing_key="notifications"),
    ],
    task_default_queue="pr_pipeline",
    task_routes={
        "app.tasks.pr_pipeline.*": {"queue": "pr_pipeline"},
        "app.tasks.indexing.*": {"queue": "indexing"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },

    # Retry / timeout settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,         # 15 min hard limit
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,

    # Result TTL
    result_expires=86400,  # 24 hours

    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-repos": {
            "task": "app.tasks.indexing.cleanup_stale_repos",
            "schedule": 3600.0,  # Every hour
        },
    },
)


# ==============================================================================
# Signals
# ==============================================================================


@setup_logging.connect
def setup_celery_logging(**kwargs: object) -> None:
    """Configure structured logging for Celery workers."""
    configure_logging()


@worker_ready.connect
def on_worker_ready(sender: object, **kwargs: object) -> None:
    """Log when a Celery worker is ready to accept tasks."""
    logger.info("Celery worker ready", worker=str(sender))
