"""TestPilot AI — Bitbucket Provider Adapter.

Implements VCSCapabilities using Bitbucket REST API v2 and Git CLI.
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


class BitbucketProvider(VCSProvider):
    """VCS Provider implementation for Bitbucket Cloud and Bitbucket Server."""

    def __init__(self) -> None:
        super().__init__(provider_name="bitbucket")

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

    def _get_auth_headers(self, credentials: VCSCredentials) -> dict[str, str]:
        if credentials.token:
            return {"Authorization": f"Bearer {credentials.token}"}
        elif credentials.username and credentials.password:
            import base64

            userpass = f"{credentials.username}:{credentials.password}".encode()
            encoded = base64.b64encode(userpass).decode("utf-8")
            return {"Authorization": f"Basic {encoded}"}
        return {}

    async def authenticate(self, credentials: VCSCredentials) -> bool:
        self._ensure_capability(VCSCapability.AUTHENTICATE)
        headers = self._get_auth_headers(credentials)
        if not headers:
            return False

        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{base_url}/user", headers=headers)
            return res.status_code == 200

    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        self._ensure_capability(VCSCapability.LIST_REPOS)
        headers = self._get_auth_headers(credentials)
        if not headers:
            return []

        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(f"{base_url}/repositories?role=member", headers=headers)
            if res.status_code != 200:
                return []

            data = res.json()
            repos = data.get("values", [])
            results = []
            for r in repos:
                clone_links = r.get("links", {}).get("clone", [])
                https_link = next(
                    (
                        link_item["href"]
                        for link_item in clone_links
                        if link_item.get("name") == "https"
                    ),
                    r.get("full_name"),
                )
                results.append(
                    VCSRepoMetadata(
                        provider_repo_id=r["full_name"],
                        name=r["name"],
                        full_name=r["full_name"],
                        owner=r.get("workspace", {}).get("slug", "workspace"),
                        clone_url=https_link,
                        default_branch=r.get("mainbranch", {}).get("name", "main"),
                        visibility="private" if r.get("is_private") else "public",
                        description=r.get("description"),
                    )
                )
            return results

    async def get_repository_metadata(
        self, repo_identifier: str, credentials: VCSCredentials | None = None
    ) -> VCSRepoMetadata:
        """Fetch Bitbucket repository metadata via API with fallback."""
        headers = self._get_auth_headers(credentials) if credentials else {}
        base_url = (
            credentials.host_url if credentials and credentials.host_url else None
        ) or "https://api.bitbucket.org/2.0"
        clean_name = (
            repo_identifier.replace("https://bitbucket.org/", "").replace(".git", "").strip("/")
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{base_url}/repositories/{clean_name}", headers=headers)
                if res.status_code == 200:
                    r = res.json()
                    clone_links = r.get("links", {}).get("clone", [])
                    https_link = next(
                        (
                            link_item["href"]
                            for link_item in clone_links
                            if link_item.get("name") == "https"
                        ),
                        f"https://bitbucket.org/{clean_name}.git",
                    )
                    return VCSRepoMetadata(
                        provider_repo_id=r.get("full_name", clean_name),
                        name=r.get("name", clean_name.split("/")[-1]),
                        full_name=r.get("full_name", clean_name),
                        owner=r.get("workspace", {}).get(
                            "slug", clean_name.split("/")[0] if "/" in clean_name else "workspace"
                        ),
                        clone_url=https_link,
                        default_branch=r.get("mainbranch", {}).get("name", "main"),
                        visibility="private" if r.get("is_private") else "public",
                        description=r.get("description") or f"Bitbucket repository {clean_name}",
                    )
        except Exception as e:
            logger.info("Bitbucket API get_repository_metadata fallback", error=str(e))

        org, repo_name = (
            clean_name.split("/")[0] if "/" in clean_name else "workspace",
            clean_name.split("/")[-1],
        )
        return VCSRepoMetadata(
            provider_repo_id=clean_name,
            name=repo_name,
            full_name=clean_name,
            owner=org,
            clone_url=f"https://bitbucket.org/{clean_name}.git",
            default_branch="main",
            visibility="public",
            description=f"Bitbucket repository {clean_name}",
        )

    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        self._ensure_capability(VCSCapability.CLONE)
        import subprocess

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        authed_url = repo_url
        if token and "bitbucket.org" in repo_url:
            authed_url = repo_url.replace("https://", f"https://x-token-auth:{token}@")

        cmd = ["git", "clone", "--depth", "1", authed_url, str(target_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 and not target_dir.exists():
            logger.warning("Bitbucket git clone failed", error=proc.stderr)
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
        headers = self._get_auth_headers(credentials)
        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/repositories/{provider_repo_id}/pullrequests/{pr_id}", headers=headers
            )
            res.raise_for_status()
            data = res.json()
            return PRMetadata(
                pr_id=str(data["id"]),
                pr_number=data["id"],
                title=data["title"],
                description=data.get("description"),
                author=data["author"]["display_name"],
                head_branch=data["source"]["branch"]["name"],
                base_branch=data["destination"]["branch"]["name"],
                head_sha=data["source"]["commit"]["hash"],
                state=data["state"].lower(),
            )

    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.CREATE_COMMENT)
        headers = self._get_auth_headers(credentials)
        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repositories/{provider_repo_id}/pullrequests/{pr_id}/comments",
                headers=headers,
                json={"content": {"raw": body_markdown}},
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
        headers = self._get_auth_headers(credentials)
        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"
        status_map = {"success": "SUCCESSFUL", "failure": "FAILED", "pending": "INPROGRESS"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repositories/{provider_repo_id}/commit/{commit_sha}/statuses/build",
                headers=headers,
                json={
                    "state": status_map.get(state, "SUCCESSFUL"),
                    "key": "TESTPILOT_AI",
                    "name": "TestPilot AI Regression Check",
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
        headers = self._get_auth_headers(credentials)
        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{base_url}/repositories/{provider_repo_id}/pullrequests",
                headers=headers,
                json={
                    "title": title,
                    "source": {"branch": {"name": head}},
                    "destination": {"branch": {"name": base}},
                    "summary": {"raw": body},
                },
            )
            res.raise_for_status()
            return str(res.json()["id"])

    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        self._ensure_capability(VCSCapability.DOWNLOAD_DIFF)
        headers = self._get_auth_headers(credentials)
        base_url = credentials.host_url or "https://api.bitbucket.org/2.0"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{base_url}/repositories/{provider_repo_id}/pullrequests/{pr_id}/diff",
                headers=headers,
            )
            res.raise_for_status()
            return res.text
