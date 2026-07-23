"""TestPilot AI — User Settings API (BYOK Gemini API Key)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import update

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import UserSettingsResponse, UserSettingsUpdate

logger = get_logger(__name__)
router = APIRouter()


def _mask_api_key(key: str) -> str:
    """Return a masked version of the API key for safe display."""
    if len(key) <= 10:
        return "••••••••••"
    return key[:6] + "•" * (len(key) - 10) + key[-4:]


def _build_settings_response(user: User) -> UserSettingsResponse:
    """Build a UserSettingsResponse from ORM user object."""
    return UserSettingsResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        has_gemini_api_key=bool(user.gemini_api_key),
        gemini_api_key_preview=_mask_api_key(user.gemini_api_key) if user.gemini_api_key else None,
    )


@router.get(
    "/me/settings",
    response_model=APIResponse[UserSettingsResponse],
    summary="Get current user settings",
)
async def get_user_settings(
    current_user: CurrentUser,
    db: DBSession,
) -> APIResponse[UserSettingsResponse]:
    """Return the authenticated user's settings including Gemini API key status."""
    return APIResponse(data=_build_settings_response(current_user))


@router.patch(
    "/me/settings",
    response_model=APIResponse[UserSettingsResponse],
    summary="Update current user settings",
)
async def update_user_settings(
    payload: UserSettingsUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> APIResponse[UserSettingsResponse]:
    """Update user settings — specifically the Gemini API key (BYOK).

    Passing `gemini_api_key: null` clears the stored key.
    """
    update_values: dict = {}

    if "gemini_api_key" in payload.model_fields_set:
        api_key = payload.gemini_api_key

        # Validate the key format (very basic)
        if api_key is not None and not api_key.startswith("AIza"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid Gemini API key format. Key must start with 'AIza'.",
            )

        update_values["gemini_api_key"] = api_key
        logger.info(
            "User updated Gemini API key",
            username=current_user.username,
            action="set" if api_key else "cleared",
        )

    if not update_values:
        return APIResponse(data=_build_settings_response(current_user))

    await db.execute(
        update(User).where(User.id == current_user.id).values(**update_values)
    )
    await db.flush()

    # Refresh user object
    await db.refresh(current_user)

    return APIResponse(
        data=_build_settings_response(current_user),
        message="Settings updated successfully.",
    )


@router.delete(
    "/me/settings/gemini-key",
    response_model=APIResponse[UserSettingsResponse],
    summary="Clear Gemini API key",
)
async def clear_gemini_api_key(
    current_user: CurrentUser,
    db: DBSession,
) -> APIResponse[UserSettingsResponse]:
    """Clears the stored Gemini API key for the current user."""
    await db.execute(
        update(User).where(User.id == current_user.id).values(gemini_api_key=None)
    )
    await db.flush()
    await db.refresh(current_user)

    logger.info("User cleared Gemini API key", username=current_user.username)

    return APIResponse(
        data=_build_settings_response(current_user),
        message="Gemini API key cleared.",
    )
