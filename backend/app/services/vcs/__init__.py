"""TestPilot AI — VCS Provider Package.

Provides a unified factory function to obtain provider adapter instances.
"""

from __future__ import annotations

from app.services.vcs.bitbucket_provider import BitbucketProvider
from app.services.vcs.generic_git_provider import GenericGitProvider
from app.services.vcs.github_provider import GitHubProvider
from app.services.vcs.gitlab_provider import GitLabProvider
from app.services.vcs.vcs_base import (
    CapabilityNotSupportedException,
    PRMetadata,
    VCSCapability,
    VCSCredentials,
    VCSProvider,
    VCSRepoMetadata,
)

_PROVIDERS: dict[str, VCSProvider] = {
    "github": GitHubProvider(),
    "bitbucket": BitbucketProvider(),
    "gitlab": GitLabProvider(),
    "custom_git": GenericGitProvider(),
}


def get_vcs_provider(provider_name: str = "github") -> VCSProvider:
    """Retrieve the VCSProvider instance for the given provider name."""
    norm_name = provider_name.lower().strip()
    return _PROVIDERS.get(norm_name, _PROVIDERS["github"])


__all__ = [
    "VCSCapability",
    "CapabilityNotSupportedException",
    "VCSCredentials",
    "VCSRepoMetadata",
    "PRMetadata",
    "VCSProvider",
    "GitHubProvider",
    "BitbucketProvider",
    "GitLabProvider",
    "GenericGitProvider",
    "get_vcs_provider",
]
