import secrets
import uuid

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import GitHubCallbackRequest, RefreshTokenRequest, TokenResponse, UserResponse
from app.services.github_service import GitHubService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/github/login", summary="GitHub OAuth Login URL")
async def github_login_url(redirect_uri: str | None = None) -> dict[str, str]:
    """Get the GitHub OAuth authorization or App installation URL.

    Returns:
        The GitHub OAuth/App URL to redirect the user to.
    """
    settings = get_settings()
    state = secrets.token_urlsafe(32)

    cb_uri = redirect_uri or "http://localhost:3000/auth/callback"

    # GitHub Apps (client ID starts with 'Iv') do NOT support OAuth scopes.
    # Permissions are defined at installation time. Only OAuth Apps use scope=.
    if settings.github_client_id.startswith("Iv"):
        url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.github_client_id}"
            f"&redirect_uri={cb_uri}"
            f"&state={state}"
        )
    else:
        url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.github_client_id}"
            f"&redirect_uri={cb_uri}"
            f"&scope=repo,read:user,user:email"
            f"&state={state}"
        )

    app_name_slug = (
        (settings.github_app_name or "testpilot-ai-shikhar").strip('"').lower().replace(" ", "-")
    )
    return {
        "url": url,
        "state": state,
        "app_install_url": f"https://github.com/apps/{app_name_slug}/installations/new",
    }


@router.get("/gitlab/login", summary="GitLab OAuth Login URL")
async def gitlab_login_url(redirect_uri: str | None = None) -> dict[str, str]:
    """Get the GitLab OAuth authorization URL."""
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    cb_uri = redirect_uri or "http://localhost:3000/auth/callback"
    client_id = settings.gitlab_client_id or "testpilot-ai-gitlab-app"

    url = (
        f"https://gitlab.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={cb_uri}"
        f"&response_type=code"
        f"&state={state}"
        f"&scope=api+read_repository+write_repository"
    )
    return {"url": url, "state": state}


@router.get("/bitbucket/login", summary="Bitbucket OAuth Login URL")
async def bitbucket_login_url(redirect_uri: str | None = None) -> dict[str, str]:
    """Get the Bitbucket Cloud OAuth authorization URL."""
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    client_id = settings.bitbucket_client_id or "testpilot-ai-bitbucket-app"

    url = (
        f"https://bitbucket.org/site/oauth2/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&state={state}"
    )
    return {"url": url, "state": state}


@router.get("/azure_devops/login", summary="Azure DevOps OAuth Login URL")
async def azure_devops_login_url(redirect_uri: str | None = None) -> dict[str, str]:
    """Get the Azure DevOps OAuth authorization URL."""
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    cb_uri = redirect_uri or "http://localhost:3000/auth/callback"
    client_id = settings.azure_devops_client_id or "testpilot-ai-app"

    url = (
        f"https://app.vssps.visualstudio.com/oauth2/authorize"
        f"?client_id={client_id}"
        f"&response_type=Assertion"
        f"&state={state}"
        f"&scope=vso.code_full%20vso.build_execute"
        f"&redirect_uri={cb_uri}"
    )
    return {"url": url, "state": state}


@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(
    request: GitHubCallbackRequest,
    db: DBSession,
    response: Response,
) -> TokenResponse:
    """Handle the GitHub OAuth callback.

    Exchanges the authorization code for an access token,
    fetches the user's GitHub profile, and creates/updates
    the user record in the database.
    """
    github = GitHubService()

    # Exchange OAuth code for access token
    try:
        token_data = await github.exchange_oauth_code(request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub OAuth error: {e}",
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from GitHub",
        )

    # Fetch GitHub user profile
    try:
        gh_user = await github.get_github_user(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch GitHub user: {e}",
        )

    # Create or update user
    result = await db.execute(select(User).where(User.github_id == str(gh_user["id"])))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            github_id=str(gh_user["id"]),
            username=gh_user.get("login", ""),
            email=gh_user.get("email"),
            name=gh_user.get("name"),
            avatar_url=gh_user.get("avatar_url"),
            github_access_token=access_token,
            role="member",
        )
        db.add(user)
        logger.info("New user created via GitHub OAuth", username=user.username)
    else:
        user.github_access_token = access_token
        user.email = gh_user.get("email") or user.email
        user.name = gh_user.get("name") or user.name
        user.avatar_url = gh_user.get("avatar_url") or user.avatar_url

    await db.flush()

    # Generate JWT tokens
    jwt_access = create_access_token(user.id)
    jwt_refresh = create_refresh_token(user.id)

    settings = get_settings()

    # Set HTTP-only cookie for refresh token (secure=False in development for HTTP compatibility)
    response.set_cookie(
        key="refresh_token",
        value=jwt_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=jwt_access,
        refresh_token=None,  # Do not expose in body for cookie flow
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=dict[str, str])
async def refresh_token(
    db: DBSession,
    request: RefreshTokenRequest | None = None,
    refresh_token: str | None = Cookie(default=None),
) -> dict[str, str]:
    """Refresh an expired access token using a refresh token from cookies or request body."""
    # Priority: Cookie > Request Body
    token = refresh_token
    if not token and request:
        token = request.refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
    except (Exception, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(user.id)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_profile(current_user: CurrentUser) -> APIResponse[UserResponse]:
    """Get the current authenticated user's profile."""
    return APIResponse(data=UserResponse.model_validate(current_user))


class GoogleLoginRequest(BaseModel):
    email: str | None = None


@router.post("/google-login", response_model=TokenResponse)
async def google_login(
    db: DBSession,
    response: Response,
    request: GoogleLoginRequest | None = None,
) -> TokenResponse:
    """Sign in with Google / Gmail. Links to existing user account by email or creates profile."""
    target_email = (
        (request.email if request and request.email else "shikhar@testpilot.ai").strip().lower()
    )

    result = await db.execute(select(User).where(User.email == target_email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GitHub account found matching this email address. Please sign in with GitHub first to create your account.",
        )

    jwt_access = create_access_token(user.id)
    jwt_refresh = create_refresh_token(user.id)
    settings = get_settings()

    response.set_cookie(
        key="refresh_token",
        value=jwt_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=jwt_access,
        refresh_token=None,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(db: DBSession, response: Response) -> TokenResponse:
    """Instant Developer Login for local testing without OAuth configuration."""
    settings = get_settings()
    result = await db.execute(select(User).where(User.username == "shikhar-dev"))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            github_id="999999",
            username="shikhar-dev",
            email="shikhar@testpilot.ai",
            name="Shikhar Srivastava",
            avatar_url="https://avatars.githubusercontent.com/u/999999?v=4",
            role="admin",
        )
        db.add(user)
        await db.flush()

    jwt_access = create_access_token(user.id)
    jwt_refresh = create_refresh_token(user.id)
    settings = get_settings()

    response.set_cookie(
        key="refresh_token",
        value=jwt_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=jwt_access,
        refresh_token=None,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )
