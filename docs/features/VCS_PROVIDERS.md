# TestPilot AI — Multi-VCS Provider Architecture & Authentication

TestPilot AI provides first-class support for listing, connecting, indexing, and reviewing repositories across multiple Version Control Systems (VCS): **GitHub**, **Bitbucket**, **GitLab**, **Azure DevOps**, and **Custom Git URLs**.

---

## 🏗️ Architecture Overview

The multi-VCS architecture is built on top of a standardized `VCSProvider` abstract base class pattern (`backend/app/services/vcs/vcs_base.py`), which abstracts provider-specific REST API calls, OAuth 2.0 authentication flows, and Git clone operations into unified system models.

```mermaid
graph TD
    Client[Frontend Connect VCS Modal] -->|HTTP Request| API[FastAPI /repositories/connect]
    
    API -->|Factory Lookup| Factory[VCS Provider Factory]
    Factory -->|instantiates| GH[GitHubProvider]
    Factory -->|instantiates| BB[BitbucketProvider]
    Factory -->|instantiates| GL[GitLabProvider]
    Factory -->|instantiates| ADO[AzureDevOpsProvider]
    Factory -->|instantiates| Custom[GenericGitProvider]
    
    GH -->|GitHub REST v3/v4| Metadata[VCSRepoMetadata Model]
    BB -->|Bitbucket REST v2| Metadata
    GL -->|GitLab REST v4| Metadata
    ADO -->|Azure DevOps REST v7.0| Metadata
    
    Metadata -->|Save Record| DB[(PostgreSQL Database)]
    Metadata -->|Queue Indexing| Task[Repository Indexer Task]
```

---

## 🔑 Supported VCS Providers & Authentication

| Provider | Metadata REST API | Auth Header Format | Git Clone Token URL Format |
| :--- | :--- | :--- | :--- |
| **GitHub** | `https://api.github.com` | `Authorization: Bearer <token>` | `https://x-access-token:{token}@github.com/owner/repo.git` |
| **Bitbucket** | `https://api.bitbucket.org/2.0` | `Authorization: Bearer <token>` | `https://x-token-auth:{token}@bitbucket.org/workspace/repo.git` |
| **GitLab** | `https://gitlab.com/api/v4` | `PRIVATE-TOKEN: <token>` | `https://oauth2:{token}@gitlab.com/group/repo.git` |
| **Azure DevOps** | `https://dev.azure.com` | `Authorization: Basic base64(:<PAT>)` | `https://{PAT}@dev.azure.com/org/project/_git/repo` |
| **Custom Git** | Generic HTTP/HTTPS | User-Provided Header | `https://{user}:{token}@custom-git.com/repo.git` |

---

## 🛡️ Security & Reliability Engineering

1. **Upfront REST API Validation**:
   - Before any repository record is saved into PostgreSQL, the target provider adapter validates the repository path against the provider's REST API.
   - Non-existent repositories (`HTTP 404`) or unauthorized private repositories (`HTTP 401/403`) return clear, immediate validation messages in the modal without leaving dead database records.

2. **Non-Interactive Git Execution**:
   - Background Git tasks operate with `GIT_TERMINAL_PROMPT="0"` and `GIT_ASKPASS="echo"`.
   - Prevents background workers from locking or waiting indefinitely for interactive credentials.

3. **Automatic Remote Branch Fallback**:
   - If a target branch (e.g. `main`) is specified but does not exist on the remote, the indexer automatically cleans the target directory and checks out the repository's native default branch (`master`, `main`, or `trunk`).

4. **1-Click OAuth 2.0 & PAT Support**:
   - Supports 1-Click OAuth 2.0 integration for enterprise team workspaces.
   - Provides optional Personal Access Token (PAT) / App Password input fields for private, internal, or self-hosted repositories.
