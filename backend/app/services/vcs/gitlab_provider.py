"""TestPilot AI — GitLab Provider Adapter.

Implements VCSCapabilities using GitLab REST API v4 and Git CLI.
"""

from __future__ import annotations

import urllib.parse
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


class GitLabProvider(VCSProvider):
    """VCS Provider implementation for GitLab.com and Self-hosted GitLab."""

    def __init__(self) -> None:
        super().__init__(provider_name="gitlab")

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

        headers = {"PRIVATE-TOKEN": credentials.token}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{base_url}/user", headers=headers)
            return res.status_code == 200

    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        self._ensure_capability(VCSCapability.LIST_REPOS)
        if not credentials.token:
            return []

        headers = {"PRIVATE-TOKEN": credentials.token}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{base_url}/projects?membership=true&order_by=updated_at&per_page=50",
                headers=headers,
            )
            if res.status_code != 200:
                return []

            repos = res.json()
            return [
                VCSRepoMetadata(
                    provider_repo_id=str(r["id"]),
                    name=r["name"],
                    full_name=r["path_with_namespace"],
                    owner=r["namespace"]["path"],
                    clone_url=r["http_url_to_repo"],
                    default_branch=r.get("default_branch", "main"),
                    visibility=r.get("visibility", "private"),
                    description=r.get("description"),
                )
                for r in repos
            ]

    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        self._ensure_capability(VCSCapability.CLONE)
        import subprocess

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        authed_url = repo_url
        if token and "gitlab.com" in repo_url:
            authed_url = repo_url.replace("https://", f"https://oauth2:{token}@")

        cmd = ["git", "clone", "--depth", "1", authed_url, str(target_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 and not target_dir.exists():
            logger.warning("GitLab git clone failed", error=proc.stderr)
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
        headers = {"PRIVATE-TOKEN": credentials.token or ""}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"
        encoded_id = urllib.parse.quote_plus(provider_repo_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/projects/{encoded_id}/merge_requests/{pr_id}", headers=headers
            )
            res.raise_for_status()
            data = res.json()
            return PRMetadata(
                pr_id=str(data["id"]),
                pr_number=data["iid"],
                title=data["title"],
                description=data.get("description"),
                author=data["author"]["username"],
                head_branch=data["source_branch"],
                base_branch=data["target_branch"],
                head_sha=data["sha"],
                state=data["state"],
            )

    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.CREATE_COMMENT)
        headers = {"PRIVATE-TOKEN": credentials.token or ""}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"
        encoded_id = urllib.parse.quote_plus(provider_repo_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/projects/{encoded_id}/merge_requests/{pr_id}/notes",
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
        headers = {"PRIVATE-TOKEN": credentials.token or ""}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"
        encoded_id = urllib.parse.quote_plus(provider_repo_id)
        status_map = {"success": "success", "failure": "failed", "pending": "running"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/projects/{encoded_id}/statuses/{commit_sha}",
                headers=headers,
                json={
                    "state": status_map.get(state, "success"),
                    "name": "TestPilot AI",
                    "description": description,
                },
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
        headers = {"PRIVATE-TOKEN": credentials.token or ""}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"
        encoded_id = urllib.parse.quote_plus(provider_repo_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/projects/{encoded_id}/merge_requests",
                headers=headers,
                json={
                    "title": title,
                    "source_branch": head,
                    "target_branch": base,
                    "description": body,
                },
            )
            res.raise_for_status()
            return str(res.json()["iid"])

    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.DOWNLOAD_DIFF)
        headers = {"PRIVATE-TOKEN": credentials.token or ""}
        base_url = credentials.host_url or "https://gitlab.com/api/v4"
        encoded_id = urllib.parse.quote_plus(provider_repo_id)

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/projects/{encoded_id}/merge_requests/{pr_id}.diff", headers=headers
            )
            res.raise_for_status()
            return res.text
