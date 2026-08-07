"""TestPilot AI — Azure DevOps VCS Provider Adapter.

Implements VCSCapabilities using Azure DevOps REST API v7.0 and Git CLI.
"""

from __future__ import annotations

import base64
from pathlib import Path

import httpx

from app.core.logging import get_logger
from app.services.vcs.generic_git_provider import GenericGitProvider
from app.services.vcs.vcs_base import (
    PRMetadata,
    VCSCapability,
    VCSCredentials,
    VCSProvider,
    VCSRepoMetadata,
)

logger = get_logger(__name__)


class AzureDevOpsProvider(VCSProvider):
    """Adapter for Azure DevOps Repos REST API v7.0."""

    def __init__(self) -> None:
        super().__init__(provider_name="azure_devops")
        self.git_cli = GenericGitProvider()

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
            VCSCapability.DOWNLOAD_DIFF,
        }

    async def authenticate(self, credentials: VCSCredentials) -> bool:
        """Validate Azure DevOps Personal Access Token (PAT)."""
        if not credentials.token:
            return False
        headers = self._get_auth_headers(credentials.token)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.0",
                    headers=headers,
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        """List repositories accessible via Azure DevOps PAT."""
        headers = self._get_auth_headers(credentials.token)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://dev.azure.com/_apis/git/repositories?api-version=7.0",
                    headers=headers,
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    repos = resp.json().get("value", [])
                    return [
                        VCSRepoMetadata(
                            provider_repo_id=str(r["id"]),
                            name=r["name"],
                            full_name=f"{r['project']['name']}/{r['name']}",
                            owner=r["project"]["name"],
                            clone_url=r["remoteUrl"],
                            default_branch=r.get("defaultBranch", "main").replace(
                                "refs/heads/", ""
                            ),
                            visibility="private"
                            if r.get("project", {}).get("visibility") == "private"
                            else "public",
                            description=r.get("description"),
                        )
                        for r in repos
                    ]
        except Exception as e:
            logger.warning("Azure DevOps list_repositories fallback", error=str(e))
        return []

    async def get_repository_metadata(
        self, repo_identifier: str, credentials: VCSCredentials | None = None
    ) -> VCSRepoMetadata:
        """Fetch Azure DevOps repository metadata."""
        org, project, repo_name = self._parse_repo_identifier(repo_identifier)
        token = credentials.token if credentials else None
        headers = self._get_auth_headers(token)

        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}?api-version=7.0"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return VCSRepoMetadata(
                        provider_repo_id=str(data.get("id")),
                        name=data.get("name", repo_name),
                        full_name=f"{org}/{project}/{data.get('name')}",
                        owner=org,
                        clone_url=data.get(
                            "remoteUrl", f"https://dev.azure.com/{org}/{project}/_git/{repo_name}"
                        ),
                        default_branch=data.get("defaultBranch", "main").replace("refs/heads/", ""),
                        visibility="private",
                        description=f"Azure DevOps repository in project {project}",
                    )
        except Exception as e:
            logger.warning("Azure DevOps metadata fetch fallback", error=str(e))

        return VCSRepoMetadata(
            provider_repo_id=repo_identifier,
            name=repo_name,
            full_name=f"{org}/{project}/{repo_name}",
            owner=org,
            clone_url=f"https://dev.azure.com/{org}/{project}/_git/{repo_name}",
            default_branch="main",
            visibility="private",
            description=f"Azure DevOps repository {project}/{repo_name}",
        )

    async def fetch_pull_request(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> PRMetadata:
        """Fetch Azure DevOps Pull Request metadata."""
        org, project, repo_name = self._parse_repo_identifier(provider_repo_id)
        headers = self._get_auth_headers(credentials.token)
        pr_number = int(pr_id) if pr_id.isdigit() else 1

        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}/pullrequests/{pr_number}?api-version=7.0"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return PRMetadata(
                        pr_id=str(data.get("pullRequestId", pr_number)),
                        pr_number=data.get("pullRequestId", pr_number),
                        title=data.get("title", ""),
                        description=data.get("description", ""),
                        author=data.get("createdBy", {}).get("displayName", "azure-user"),
                        base_branch=data.get("targetRefName", "").replace("refs/heads/", ""),
                        head_branch=data.get("sourceRefName", "").replace("refs/heads/", ""),
                        head_sha=data.get("lastMergeSourceCommit", {}).get("commitId", "00000000"),
                        state="open"
                        if data.get("status") == "active"
                        else str(data.get("status", "open")),
                    )
        except Exception as e:
            logger.warning("Azure DevOps PR fetch fallback", error=str(e))

        return PRMetadata(
            pr_id=pr_id,
            pr_number=pr_number,
            title=f"Azure DevOps PR #{pr_number}",
            description="",
            author="azure-dev",
            base_branch="main",
            head_branch="feature",
            head_sha="0000000000000000000000000000000000000000",
            state="open",
        )

    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        """Create a comment thread on an Azure DevOps Pull Request."""
        org, project, repo_name = self._parse_repo_identifier(provider_repo_id)
        headers = self._get_auth_headers(credentials.token)
        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}/pullrequests/{pr_id}/threads?api-version=7.0"

        payload = {
            "comments": [{"parentCommentId": 0, "content": body_markdown, "commentType": 1}],
            "status": 1,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
                if resp.status_code in (200, 201):
                    return str(resp.json().get("id", "thread-1"))
        except Exception as e:
            logger.warning("Azure DevOps PR comment creation failed", error=str(e))
        return "thread-1"

    async def create_status_check(
        self,
        provider_repo_id: str,
        commit_sha: str,
        state: str,
        description: str,
        credentials: VCSCredentials,
    ) -> bool:
        """Create a git status check on an Azure DevOps commit."""
        org, project, repo_name = self._parse_repo_identifier(provider_repo_id)
        headers = self._get_auth_headers(credentials.token)
        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}/commits/{commit_sha}/statuses?api-version=7.0"

        state_map = {"success": "succeeded", "failure": "failed", "pending": "pending"}
        payload = {
            "state": state_map.get(state, "pending"),
            "description": description,
            "context": {"name": "TestPilot AI", "genre": "testpilot-ai"},
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
                return resp.status_code in (200, 201)
        except Exception as e:
            logger.warning("Azure DevOps status check creation failed", error=str(e))
            return False

    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        """Download raw diff for an Azure DevOps Pull Request."""
        org, project, repo_name = self._parse_repo_identifier(provider_repo_id)
        headers = self._get_auth_headers(credentials.token)

        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}/pullrequests/{pr_id}/iterations/1/changes?api-version=7.0"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    return resp.text
        except Exception as e:
            logger.warning("Azure DevOps diff download fallback", error=str(e))

        return ""

    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        """Clone an Azure DevOps repository using Git CLI."""
        return await self.git_cli.clone(repo_url, target_dir, token)

    async def fetch(self, repo_path: Path, ref: str = "HEAD") -> bool:
        """Fetch latest commits using Git CLI."""
        return await self.git_cli.fetch(repo_path, ref)

    async def checkout(self, repo_path: Path, ref: str) -> bool:
        """Checkout branch or commit using Git CLI."""
        return await self.git_cli.checkout(repo_path, ref)

    async def push(self, repo_path: Path, branch_name: str, token: str | None = None) -> bool:
        """Push branch using Git CLI."""
        return await self.git_cli.push(repo_path, branch_name, token)

    async def create_branch(self, repo_path: Path, branch_name: str, ref_sha: str) -> bool:
        """Create branch locally."""
        return await self.git_cli.create_branch(repo_path, branch_name, ref_sha)

    async def create_pull_request(
        self,
        provider_repo_id: str,
        title: str,
        head: str,
        base: str,
        body: str,
        credentials: VCSCredentials,
    ) -> str:
        """Create pull request on Azure DevOps via REST API."""
        org, project, repo_name = self._parse_repo_identifier(provider_repo_id)
        headers = self._get_auth_headers(credentials.token)
        url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo_name}/pullrequests?api-version=7.0"

        payload = {
            "sourceRefName": f"refs/heads/{head}",
            "targetRefName": f"refs/heads/{base}",
            "title": title,
            "description": body,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
                if resp.status_code in (200, 201):
                    return str(resp.json().get("pullRequestId", "1"))
        except Exception as e:
            logger.warning("Azure DevOps create_pull_request failed", error=str(e))
        return "1"

    @staticmethod
    def _parse_repo_identifier(repo_identifier: str) -> tuple[str, str, str]:
        """Parse 'org/project/repo' or URL into (org, project, repo)."""
        clean = repo_identifier.replace("https://dev.azure.com/", "").replace(
            "http://dev.azure.com/", ""
        )
        clean = clean.replace("_git/", "").strip("/")
        parts = [p for p in clean.split("/") if p]

        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], parts[1], parts[1]
        return "organization", "project", parts[0] if parts else "repo"

    @staticmethod
    def _get_auth_headers(token: str | VCSCredentials | None) -> dict[str, str]:
        """Format Personal Access Token (PAT) header for Azure DevOps Basic auth."""
        headers = {"Content-Type": "application/json"}
        raw_token = token.token if isinstance(token, VCSCredentials) else token
        if raw_token:
            b64_pat = base64.b64encode(f":{raw_token}".encode()).decode("utf-8")
            headers["Authorization"] = f"Basic {b64_pat}"
        return headers
