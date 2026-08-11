"""TestPilot AI — Unified Multi-VCS Webhook Router."""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.api.deps import DBSession
from app.core.logging import get_logger
from app.services.idempotency import IdempotencyService
from app.utils.webhook_adapters import get_webhook_adapter

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{provider}", status_code=status.HTTP_202_ACCEPTED)
async def handle_vcs_webhook(
    provider: str,
    request: Request,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Unified Webhook endpoint for GitHub, Bitbucket, GitLab, and Azure DevOps.

    Sequence:
    1. Lookup WebhookAdapter for target VCS provider.
    2. Verify HMAC signature / shared secret token (401 on invalid signature).
    3. Extract delivery ID & parse NormalizedPREvent payload (400 on malformed payload).
    4. Check IdempotencyService lock (202 Accepted with duplicate warning if repeated delivery).
    5. Enqueue PR analysis background task.
    6. Return HTTP 202 Accepted (Target SLA: p95 < 200ms).
    """
    recv_time = time.monotonic()
    headers_dict = dict(request.headers)
    body_bytes = await request.body()

    # 1. Lookup provider adapter
    try:
        adapter = get_webhook_adapter(provider)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported VCS webhook provider '{provider}': {e}",
        )

    # 2. Security Verification
    if not adapter.verify(headers_dict, body_bytes):
        logger.warning(
            "Webhook signature verification failed",
            provider=provider,
            client_host=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid webhook signature or secret token for provider '{provider}'.",
        )

    # 3. Parse NormalizedPREvent
    try:
        event = adapter.parse(headers_dict, body_bytes)
    except Exception as e:
        logger.error("Failed to parse webhook payload", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed webhook payload for provider '{provider}': {e}",
        )

    # 4. Idempotency Lock Check
    is_new = await IdempotencyService.check_and_lock(
        provider=event.provider,
        repository=event.repository,
        delivery_id=event.delivery_id,
    )
    if not is_new:
        logger.info(
            "Duplicate webhook delivery suppressed",
            provider=event.provider,
            repository=event.repository,
            delivery_id=event.delivery_id,
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "success": True,
                "message": f"Duplicate webhook delivery '{event.delivery_id}' suppressed.",
                "data": event.model_dump(),
            },
        )

    # 5. Enqueue background PR analysis
    ack_latency_ms = int((time.monotonic() - recv_time) * 1000)
    logger.info(
        "Webhook accepted and enqueued",
        provider=event.provider,
        repository=event.repository,
        action=event.action,
        delivery_id=event.delivery_id,
        ack_latency_ms=ack_latency_ms,
    )

    # Enqueue pipeline task asynchronously
    try:
        from app.tasks.pr_pipeline import analyze_pull_request

        analyze_pull_request.delay(
            repository_full_name=event.repository,
            pull_request_number=int(event.pull_request_id)
            if event.pull_request_id.isdigit()
            else 1,
            provider=event.provider,
            head_sha=event.head_sha,
            base_sha=event.base_sha,
            source_branch=event.source_branch,
            target_branch=event.target_branch,
            webhook_received_time=recv_time,
        )
    except Exception as e:
        logger.warning(
            "Celery dispatch fallback to FastAPI background task for webhook",
            error=str(e),
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "success": True,
            "message": f"Webhook event '{event.action}' for repository '{event.repository}' accepted and enqueued.",
            "data": event.model_dump(),
        },
    )
