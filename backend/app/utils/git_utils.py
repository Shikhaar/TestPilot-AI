"""
TestPilot AI — Git Utilities.

Provides helper functions for cloning, pulling, and working with Git repositories
using GitPython.
"""

from __future__ import annotations

from pathlib import Path

import git

from app.core.logging import get_logger

logger = get_logger(__name__)


def clone_repository(clone_url: str, dest_path: Path, access_token: str | None = None) -> git.Repo:
    """Clone a Git repository to the specified destination path.

    Args:
        clone_url: The git clone URL.
        dest_path: Destination path on the local system.
        access_token: Optional OAuth access token for authorization.

    Returns:
        The GitPython Repo object.
    """
    if access_token and "github.com" in clone_url:
        clone_url = clone_url.replace("https://", f"https://x-access-token:{access_token}@")

    logger.info(
        "Cloning Git repository",
        url=clone_url.replace(access_token or "", "***") if access_token else clone_url,
        dest=str(dest_path),
    )
    dest_path.mkdir(parents=True, exist_ok=True)
    return git.Repo.clone_from(clone_url, dest_path, depth=50)


def update_repository(repo_path: Path) -> git.Repo:
    """Pull the latest changes for an already cloned Git repository.

    Args:
        repo_path: Local path to the repository.

    Returns:
        The updated GitPython Repo object.
    """
    logger.info("Updating Git repository", path=str(repo_path))
    repo = git.Repo(repo_path)
    origin = repo.remotes.origin
    origin.pull()
    return repo


def get_diff(repo_path: Path, base_sha: str, head_sha: str) -> str:
    """Get the git diff between two commit hashes.

    Args:
        repo_path: Local path to the repository.
        base_sha: The base commit SHA.
        head_sha: The head commit SHA.

    Returns:
        The text diff.
    """
    repo = git.Repo(repo_path)
    return repo.git.diff(base_sha, head_sha)
