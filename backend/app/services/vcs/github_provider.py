"""TestPilot AI — GitHub Provider Adapter.

Implements all VCSCapabilities using GitHub REST API and Git CLI.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vcs.vcs_base import (
    PRMetadata,
    VCSCapability,
    VCSCredentials,
    VCSProvider,
    VCSRepoMetadata,
)

logger = get_logger(__name__)
settings = get_settings()


class GitHubProvider(VCSProvider):
    """VCS Provider implementation for GitHub and GitHub Enterprise."""

    def __init__(self) -> None:
        super().__init__(provider_name="github")

    def get_capabilities(self) -> set[VCSCapability]:
        return {
            VCSCapability.AUTHENTICATE,
            VCSCapability.LIST_REPOS,
            VCSCapability.CLONE,
            VCSCapability.FETCH,
            VCSCapability.PUSH,
            VCSCapability.CHECKOUT,
            VCSCapability.FETCH_PR,
            VCSCapability.CREATE_COMMENT,
            VCSCapability.CREATE_STATUS_CHECK,
            VCSCapability.CREATE_BRANCH,
            VCSCapability.CREATE_PR,
            VCSCapability.DOWNLOAD_DIFF,
        }

    async def authenticate(self, credentials: VCSCredentials) -> bool:
        self._ensure_capability(VCSCapability.AUTHENTICATE)
        if not credentials.token:
            return False

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{base_url}/user", headers=headers)
            return res.status_code == 200

    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        self._ensure_capability(VCSCapability.LIST_REPOS)
        if not credentials.token:
            return []

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{base_url}/user/repos?sort=updated&per_page=50", headers=headers
            )
            if res.status_code != 200:
                return []

            repos = res.json()
            return [
                VCSRepoMetadata(
                    provider_repo_id=str(r["id"]),
                    name=r["name"],
                    full_name=r["full_name"],
                    owner=r["owner"]["login"],
                    clone_url=r["clone_url"],
                    default_branch=r.get("default_branch", "main"),
                    visibility="private" if r.get("private") else "public",
                    description=r.get("description"),
                )
                for r in repos
            ]

    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        self._ensure_capability(VCSCapability.CLONE)
        import subprocess

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        authed_url = repo_url
        if token and "github.com" in repo_url:
            authed_url = repo_url.replace("https://", f"https://x-access-token:{token}@")

        cmd = ["git", "clone", "--depth", "1", authed_url, str(target_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 and not target_dir.exists():
            logger.warning("Git clone failed", error=proc.stderr)
        return target_dir

    async def fetch(self, repo_path: Path, ref: str = "HEAD") -> bool:
        self._ensure_capability(VCSCapability.FETCH)
        import subprocess

        cmd = ["git", "-C", str(repo_path), "fetch", "origin", ref]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def push(self, repo_path: Path, branch_name: str, token: str | None = None) -> bool:
        self._ensure_capability(VCSCapability.PUSH)
        import subprocess

        cmd = ["git", "-C", str(repo_path), "push", "-u", "origin", branch_name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def checkout(self, repo_path: Path, ref: str) -> bool:
        self._ensure_capability(VCSCapability.CHECKOUT)
        import subprocess

        cmd = ["git", "-C", str(repo_path), "checkout", ref]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    async def fetch_pull_request(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> PRMetadata:
        self._ensure_capability(VCSCapability.FETCH_PR)
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/repos/{provider_repo_id}/pulls/{pr_id}", headers=headers
            )
            res.raise_for_status()
            data = res.json()
            return PRMetadata(
                pr_id=str(data["id"]),
                pr_number=data["number"],
                title=data["title"],
                description=data.get("body"),
                author=data["user"]["login"],
                head_branch=data["head"]["ref"],
                base_branch=data["base"]["ref"],
                head_sha=data["head"]["sha"],
                state=data["state"],
            )

    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.CREATE_COMMENT)
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repos/{provider_repo_id}/issues/{pr_id}/comments",
                headers=headers,
                json={"body": body_markdown},
            )
            res.raise_for_status()
            return str(res.json()["id"])

    async def create_status_check(
        self,
        provider_repo_id: str,
        commit_sha: str,
        state: str,
        description: str,
        credentials: VCSCredentials,
    ) -> bool:
        self._ensure_capability(VCSCapability.CREATE_STATUS_CHECK)
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repos/{provider_repo_id}/statuses/{commit_sha}",
                headers=headers,
                json={"state": state, "description": description, "context": "TestPilot AI"},
            )
            return res.status_code in (200, 201)

    async def create_branch(self, repo_path: Path, branch_name: str, ref_sha: str) -> bool:
        self._ensure_capability(VCSCapability.CREATE_BRANCH)
        import subprocess

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
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repos/{provider_repo_id}/pulls",
                headers=headers,
                json={"title": title, "head": head, "base": base, "body": body},
            )
            res.raise_for_status()
            return str(res.json()["number"])

    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.DOWNLOAD_DIFF)
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/vnd.github.v3.diff",
        }
        base_url = credentials.host_url or "https://api.github.com"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/repos/{provider_repo_id}/pulls/{pr_id}", headers=headers
            )
            res.raise_for_status()
            return res.text
