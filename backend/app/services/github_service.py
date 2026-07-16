"""
TestPilot AI — GitHub Service.

Handles all GitHub API interactions:
- GitHub App JWT authentication
- Installation access tokens
- Repository metadata fetching
- Pull Request data extraction
- Webhook signature verification
- Posting PR reviews and status checks
- GitHub OAuth flow

Uses PyGitHub with custom JWT auth for GitHub App authentication.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from github import Auth, Github, GithubException, GithubIntegration
from github.PullRequest import PullRequest as GithubPR
from github.Repository import Repository as GithubRepo

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.pull_request import ChangedFile, DiffSummary

logger = get_logger(__name__)
settings = get_settings()


class GitHubService:
    """Service layer for GitHub API operations.

    Uses GitHub App authentication (JWT + Installation Token) for
    server-to-server API calls. Falls back to OAuth tokens for
    user-authenticated calls.

    Attributes:
        _integration: PyGitHub GithubIntegration instance for App auth.
    """

    def __init__(self) -> None:
        self._integration: GithubIntegration | None = None
        self._init_integration()

    def _init_integration(self) -> None:
        """Initialize the GitHub App integration.

        Only initializes if APP_ID and PRIVATE_KEY are configured.
        In development with placeholder values, this is a no-op.
        """
        if not settings.github_app_id or not settings.github_private_key:
            logger.warning(
                "GitHub App not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY_PATH "
                "to enable GitHub App authentication."
            )
            return

        try:
            auth = Auth.AppAuth(
                app_id=int(settings.github_app_id),
                private_key=settings.github_private_key,
            )
            self._integration = GithubIntegration(auth=auth)
            logger.info("GitHub App integration initialized", app_id=settings.github_app_id)
        except Exception as e:
            logger.error("Failed to initialize GitHub App integration", error=str(e))

    def get_installation_client(self, installation_id: str) -> Github:
        """Get a GitHub client authenticated as a specific app installation.

        Args:
            installation_id: The GitHub App installation ID.

        Returns:
            A PyGitHub client with installation-level access.

        Raises:
            RuntimeError: If GitHub App is not configured.
        """
        if self._integration is None:
            raise RuntimeError(
                "GitHub App integration not initialized. Configure GITHUB_APP_ID and PRIVATE_KEY."
            )

        auth = self._integration.get_app_installation(int(installation_id)).get_github_for_installation()
        return auth

    def get_user_client(self, access_token: str) -> Github:
        """Get a GitHub client authenticated with a user's OAuth token.

        Args:
            access_token: The user's GitHub OAuth access token.

        Returns:
            A PyGitHub client with user-level access.
        """
        return Github(auth=Auth.Token(access_token))

    async def exchange_oauth_code(self, code: str) -> dict[str, Any]:
        """Exchange a GitHub OAuth authorization code for an access token.

        Args:
            code: The OAuth authorization code from the callback.

        Returns:
            Dictionary containing access_token, scope, token_type.

        Raises:
            httpx.HTTPStatusError: If the token exchange fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise ValueError(f"GitHub OAuth error: {data['error']}: {data.get('error_description')}")

            logger.info("GitHub OAuth code exchanged successfully")
            return data

    async def get_github_user(self, access_token: str) -> dict[str, Any]:
        """Fetch the authenticated user's GitHub profile.

        Args:
            access_token: The user's GitHub OAuth access token.

        Returns:
            Dictionary with GitHub user profile data.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            return response.json()

    def get_repository(
        self,
        full_name: str,
        access_token: str | None = None,
        installation_id: str | None = None,
    ) -> GithubRepo:
        """Fetch a GitHub repository by full name.

        Args:
            full_name: GitHub full name (e.g., 'owner/repo').
            access_token: User OAuth token (for user-authenticated calls).
            installation_id: App installation ID (for app-authenticated calls).

        Returns:
            PyGitHub Repository object.

        Raises:
            GithubException: If the repository is not found or inaccessible.
        """
        client = self._get_client(access_token, installation_id)
        return client.get_repo(full_name)

    def get_pull_request(
        self,
        repo_full_name: str,
        pr_number: int,
        access_token: str | None = None,
        installation_id: str | None = None,
    ) -> GithubPR:
        """Fetch a specific pull request.

        Args:
            repo_full_name: GitHub full name of the repository.
            pr_number: GitHub PR number.
            access_token: User OAuth token.
            installation_id: App installation ID.

        Returns:
            PyGitHub PullRequest object.
        """
        repo = self.get_repository(repo_full_name, access_token, installation_id)
        return repo.get_pull(pr_number)

    def extract_diff_summary(self, pr: GithubPR) -> DiffSummary:
        """Extract a structured diff summary from a GitHub PullRequest.

        Parses changed files, additions, deletions, and identifies
        the programming languages involved.

        Args:
            pr: PyGitHub PullRequest object.

        Returns:
            Structured DiffSummary schema.
        """
        changed_files = []
        affected_languages = set()

        for file in pr.get_files():
            changed_files.append(
                ChangedFile(
                    path=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    old_path=file.previous_filename,
                )
            )
            # Detect language from file extension
            lang = self._detect_language_from_path(file.filename)
            if lang:
                affected_languages.add(lang)

        return DiffSummary(
            changed_files=changed_files,
            total_additions=pr.additions,
            total_deletions=pr.deletions,
            affected_languages=list(affected_languages),
            changed_functions=[],  # Populated by AST parser later
            changed_classes=[],
            changed_routes=[],
        )

    def post_pr_review(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        access_token: str | None = None,
        installation_id: str | None = None,
    ) -> dict[str, Any]:
        """Post a review comment to a GitHub Pull Request.

        Args:
            repo_full_name: GitHub full name of the repository.
            pr_number: PR number.
            body: Markdown-formatted review body.
            event: 'COMMENT' | 'APPROVE' | 'REQUEST_CHANGES'.
            access_token: User OAuth token.
            installation_id: App installation ID.

        Returns:
            Dictionary with review ID and HTML URL.
        """
        repo = self.get_repository(repo_full_name, access_token, installation_id)
        pr = repo.get_pull(pr_number)
        review = pr.create_review(body=body, event=event)

        logger.info(
            "Posted PR review",
            repo=repo_full_name,
            pr_number=pr_number,
            review_id=review.id,
            event=event,
        )
        return {"review_id": str(review.id), "html_url": review.html_url}

    def create_check_run(
        self,
        repo_full_name: str,
        head_sha: str,
        name: str,
        status: str,
        conclusion: str | None = None,
        output: dict[str, Any] | None = None,
        installation_id: str | None = None,
    ) -> int:
        """Create or update a GitHub Check Run.

        Args:
            repo_full_name: Repository full name.
            head_sha: The commit SHA to attach the check to.
            name: Check run name displayed on GitHub.
            status: 'queued' | 'in_progress' | 'completed'.
            conclusion: Required when status='completed'. 'success' | 'failure' | 'neutral'.
            output: Optional dict with 'title', 'summary', 'text' for detailed output.
            installation_id: App installation ID.

        Returns:
            The check run ID.
        """
        client = self._get_client(installation_id=installation_id)
        repo = client.get_repo(repo_full_name)

        kwargs: dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
        }
        if conclusion:
            kwargs["conclusion"] = conclusion
        if output:
            kwargs["output"] = output

        check_run = repo.create_check_run(**kwargs)
        logger.info("Created check run", repo=repo_full_name, check_run_id=check_run.id)
        return check_run.id

    def _get_client(
        self,
        access_token: str | None = None,
        installation_id: str | None = None,
    ) -> Github:
        """Get the appropriate GitHub client.

        Priority: installation_id > access_token > unauthenticated.
        """
        if installation_id and self._integration:
            return self.get_installation_client(installation_id)
        if access_token:
            return self.get_user_client(access_token)
        return Github()

    @staticmethod
    def _detect_language_from_path(file_path: str) -> str | None:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".jsx": "JavaScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".cs": "C#",
            ".cpp": "C++",
            ".c": "C",
            ".php": "PHP",
            ".kt": "Kotlin",
            ".swift": "Swift",
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return None
