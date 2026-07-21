"""TestPilot AI — WebSocket Endpoints for Real-time Streaming."""

from __future__ import annotations

import contextlib
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/pr/{pr_id}")
async def websocket_pr_updates(websocket: WebSocket, pr_id: str) -> None:
    """WebSocket endpoint for real-time PR analysis progress updates.

    Streams:
    - Agent start/completion events
    - Risk score updates
    - Test generation progress
    - Final review

    Usage:
        ws://localhost:8000/ws/pr/{pr_id}

    Message format:
        {"event": "agent_started", "agent": "diff_agent", "timestamp": "..."}
        {"event": "agent_completed", "agent": "diff_agent", "data": {...}}
        {"event": "pipeline_completed", "risk_level": "high", "score": 7.2}
        {"event": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info("WebSocket connection opened", pr_id=pr_id)

    try:
        import redis.asyncio as aioredis

        from app.core.config import get_settings

        settings = get_settings()

        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"pr_updates:{pr_id}")

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "event": "connected",
                "pr_id": pr_id,
                "message": "Subscribed to PR analysis updates",
            }
        )

        # Listen for updates from Redis pub/sub
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)

                    # Close when pipeline completes
                    if data.get("event") in ("pipeline_completed", "pipeline_failed"):
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

        await pubsub.unsubscribe(f"pr_updates:{pr_id}")
        await redis.aclose()  # type: ignore[attr-defined]

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected", pr_id=pr_id)
    except Exception as e:
        logger.exception("WebSocket error", pr_id=pr_id, error=str(e))
        with contextlib.suppress(Exception):
            await websocket.send_json({"event": "error", "message": str(e)})
    finally:
        logger.info("WebSocket connection closed", pr_id=pr_id)


@ws_router.websocket("/indexing/{repo_id}")
async def websocket_indexing_progress(websocket: WebSocket, repo_id: str) -> None:
    """WebSocket endpoint for repository indexing progress.

    Streams:
    - Files parsed count
    - Current stage (cloning, parsing, embedding)
    - Completion percentage
    - Final indexed stats
    """
    await websocket.accept()
    logger.info("Indexing WebSocket opened", repo_id=repo_id)

    try:
        import redis.asyncio as aioredis

        from app.core.config import get_settings

        settings = get_settings()

        redis = aioredis.from_url(settings.redis_url)
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"indexing:{repo_id}")

        await websocket.send_json(
            {
                "event": "connected",
                "repo_id": repo_id,
            }
        )

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                    if data.get("event") in ("indexing_completed", "indexing_failed"):
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

        await pubsub.unsubscribe(f"indexing:{repo_id}")
        await redis.aclose()  # type: ignore[attr-defined]

    except WebSocketDisconnect:
        logger.info("Indexing WebSocket client disconnected", repo_id=repo_id)
    except Exception as e:
        logger.exception("Indexing WebSocket error", repo_id=repo_id, error=str(e))
