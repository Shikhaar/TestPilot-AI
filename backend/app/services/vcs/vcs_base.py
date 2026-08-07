"""TestPilot AI — Multi-VCS Base Classes & Capability Enum.

Defines the abstract interface for VCS providers (GitHub, Bitbucket, GitLab, Generic Git).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class VCSCapability(str, Enum):
    """Supported platform capabilities for VCS providers."""

    AUTHENTICATE = "vcs.authenticate"
    LIST_REPOS = "vcs.list_repos"
    CLONE = "vcs.clone"
    FETCH = "vcs.fetch"
    PUSH = "vcs.push"
    CHECKOUT = "vcs.checkout"
    FETCH_PR = "vcs.fetch_pr"
    CREATE_COMMENT = "vcs.create_comment"
    CREATE_STATUS_CHECK = "vcs.create_status_check"
    CREATE_BRANCH = "vcs.create_branch"
    CREATE_PR = "vcs.create_pr"
    DOWNLOAD_DIFF = "vcs.download_diff"


class CapabilityNotSupportedException(Exception):
    """Raised when an operation is requested on a provider lacking that capability."""

    def __init__(self, provider_name: str, capability: VCSCapability) -> None:
        self.provider_name = provider_name
        self.capability = capability
        super().__init__(
            f"Provider '{provider_name}' does not support capability '{capability.value}'"
        )


class VCSCredentials(BaseModel):
    """Credentials used for authenticating against a VCS provider."""

    provider: str = Field(description="github | bitbucket | gitlab | custom_git")
    token: str | None = Field(
        default=None, description="OAuth token or Personal Access Token (PAT)"
    )
    username: str | None = Field(default=None, description="Username or app client ID")
    password: str | None = Field(default=None, description="App password or client secret")
    host_url: str | None = Field(default=None, description="Self-hosted URL endpoint if applicable")


class VCSRepoMetadata(BaseModel):
    """Standardized metadata representation for a repository from any VCS provider."""

    provider_repo_id: str
    name: str
    full_name: str
    owner: str
    clone_url: str
    default_branch: str = "main"
    visibility: str = "private"  # public | private | internal
    description: str | None = None


class PRMetadata(BaseModel):
    """Standardized metadata representation for a Pull Request across any VCS provider."""

    pr_id: str
    pr_number: int
    title: str
    description: str | None = None
    author: str
    head_branch: str
    base_branch: str
    head_sha: str
    state: str = "open"  # open | merged | closed


class VCSProvider(ABC):
    """Abstract base class for VCS Provider adapters."""

    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    @abstractmethod
    def get_capabilities(self) -> set[VCSCapability]:
        """Return the set of capabilities supported by this provider."""
        ...

    def supports(self, capability: VCSCapability) -> bool:
        """Check whether this provider supports a specific capability."""
        return capability in self.get_capabilities()

    def _ensure_capability(self, capability: VCSCapability) -> None:
        """Raise CapabilityNotSupportedException if capability is not supported."""
        if not self.supports(capability):
            raise CapabilityNotSupportedException(self.provider_name, capability)

    @abstractmethod
    async def authenticate(self, credentials: VCSCredentials) -> bool:
        """Authenticate against the VCS API or server."""
        ...

    @abstractmethod
    async def list_repositories(self, credentials: VCSCredentials) -> list[VCSRepoMetadata]:
        """List repositories accessible to the authenticated user/token."""
        ...

    async def get_repository_metadata(
        self, repo_identifier: str, credentials: VCSCredentials | None = None
    ) -> VCSRepoMetadata:
        """Fetch standardized repository metadata."""
        org, repo_name = (
            repo_identifier.split("/")[0] if "/" in repo_identifier else "owner",
            repo_identifier.split("/")[-1],
        )
        return VCSRepoMetadata(
            provider_repo_id=repo_identifier,
            name=repo_name,
            full_name=repo_identifier,
            owner=org,
            clone_url=f"https://{self.provider_name}.org/{repo_identifier}.git",
            default_branch="main",
            visibility="private",
            description=f"{self.provider_name.capitalize()} repository {repo_identifier}",
        )

    @abstractmethod
    async def clone(self, repo_url: str, target_dir: Path, token: str | None = None) -> Path:
        """Clone a remote repository to local target directory."""
        ...

    @abstractmethod
    async def fetch(self, repo_path: Path, ref: str = "HEAD") -> bool:
        """Fetch updates from remote repository."""
        ...

    @abstractmethod
    async def push(self, repo_path: Path, branch_name: str, token: str | None = None) -> bool:
        """Push local commits to remote branch."""
        ...

    @abstractmethod
    async def checkout(self, repo_path: Path, ref: str) -> bool:
        """Checkout a specific branch or ref in local repository."""
        ...

    @abstractmethod
    async def fetch_pull_request(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> PRMetadata:
        """Fetch metadata for a pull request / merge request."""
        ...

    @abstractmethod
    async def create_comment(
        self, provider_repo_id: str, pr_id: str, body_markdown: str, credentials: VCSCredentials
    ) -> str:
        """Create a markdown comment on a pull request / merge request."""
        ...

    @abstractmethod
    async def create_status_check(
        self,
        provider_repo_id: str,
        commit_sha: str,
        state: str,
        description: str,
        credentials: VCSCredentials,
    ) -> bool:
        """Post a commit status check (success/failure/pending)."""
        ...

    @abstractmethod
    async def create_branch(self, repo_path: Path, branch_name: str, ref_sha: str) -> bool:
        """Create a new branch locally or remotely."""
        ...

    @abstractmethod
    async def create_pull_request(
        self,
        provider_repo_id: str,
        title: str,
        head: str,
        base: str,
        body: str,
        credentials: VCSCredentials,
    ) -> str:
        """Create a pull request / merge request on the provider."""
        ...

    @abstractmethod
    async def download_diff(
        self, provider_repo_id: str, pr_id: str, credentials: VCSCredentials
    ) -> str:
        """Download raw diff content for a pull request / merge request."""
        ...
