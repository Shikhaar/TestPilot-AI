"""TestPilot AI — Generic Git Provider Adapter.

Implements core Git CLI capabilities (clone, fetch, push, checkout) for arbitrary Git URLs.
Raises CapabilityNotSupportedException for PR/API specific operations.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.logging import get_logger
from app.services.vcs.vcs_base import (
    PRMetadata,
    VCSCapability,
    VCSCredentials,
    VCSProvider,
    VCSRepoMetadata,
)

logger = get_logger(__name__)


class GenericGitProvider(VCSProvider):
    """VCS Provider implementation for generic Git URLs."""

    def __init__(self) -> None:
        super().__init__(provider_name="custom_git")

    def get_capabilities(self) -> set[VCSCapability]:
        return {
            VCSCapability.AUTHENTICATE,
            VCSCapability.CLONE,
            VCSCapability.FETCH,
            VCSCapability.PUSH,
            VCSCapability.CHECKOUT,
        }

    async def authenticate(self, credentials: VCSCredentials) -> bool:
        self._ensure_capability(VCSCapability.AUTHENTICATE)
        return True  # Generic URLs authenticate upon clone

    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        self._ensure_capability(VCSCapability.LIST_REPOS)
        return []

    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        self._ensure_capability(VCSCapability.CLONE)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        authed_url = repo_url
        if token and "https://" in repo_url:
            authed_url = repo_url.replace("https://", f"https://oauth2:{token}@")

        cmd = ["git", "clone", "--depth", "1", authed_url, str(target_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 and not target_dir.exists():
            logger.warning("Generic git clone failed", error=proc.stderr)
        return target_dir

    async def fetch(self, repo_path: Path, ref: str = "HEAD") -> bool:
        self._ensure_capability(VCSCapability.FETCH)
        cmd = ["git", "-C", str(repo_path), "fetch", "origin", ref]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def push(self, repo_path: Path, branch_name: str, token: str | None = None) -> bool:
        self._ensure_capability(VCSCapability.PUSH)
        cmd = ["git", "-C", str(repo_path), "push", "-u", "origin", branch_name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def checkout(self, repo_path: Path, ref: str) -> bool:
        self._ensure_capability(VCSCapability.CHECKOUT)
        cmd = ["git", "-C", str(repo_path), "checkout", ref]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def fetch_pull_request(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> PRMetadata:
        self._ensure_capability(VCSCapability.FETCH_PR)
        raise NotImplementedError

    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.CREATE_COMMENT)
        raise NotImplementedError

    async def create_status_check(
        self,
        provider_repo_id: str,
        commit_sha: str,
        state: str,
        description: str,
        credentials: VCSCredentials,
    ) -> bool:
        self._ensure_capability(VCSCapability.CREATE_STATUS_CHECK)
        raise NotImplementedError

    async def create_branch(self, repo_path: Path, branch_name: str, ref_sha: str) -> bool:
        self._ensure_capability(VCSCapability.CREATE_BRANCH)
        cmd = ["git", "-C", str(repo_path), "checkout", "-b", branch_name, ref_sha]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def create_pull_request(
        self,
        provider_repo_id: str,
        title: str,
        head: str,
        base: str,
        body: str,
        credentials: VCSCredentials,
    ) -> str:
        self._ensure_capability(VCSCapability.CREATE_PR)
        raise NotImplementedError

    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.DOWNLOAD_DIFF)
        raise NotImplementedError
