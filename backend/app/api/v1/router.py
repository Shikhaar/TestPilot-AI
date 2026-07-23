"""TestPilot AI — API v1 Router."""

from fastapi import APIRouter

from app.api.v1 import ai, auth, dashboard, pull_requests, repositories, tests, users, webhooks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(pull_requests.router, prefix="/pr", tags=["Pull Requests"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
