# TestPilot AI — System Task List

## Phase 1: Backend Foundation (Completed)
- [x] `docker-compose.yml`
- [x] `docker-compose.override.yml`
- [x] `.env.example`
- [x] `Makefile`
- [x] `README.md`
- [x] `.gitignore`
- [x] `.github/workflows/ci.yml`
- [x] FastAPI setups, models, repositories, schemas, services, agents, celery workers/tasks, webhooks.

## Phase 2: AI Core (Completed)
- [x] Tree-sitter parsing integration (ast_parser)
- [x] Dependency Graph traversals (dependency_graph_builder)
- [x] Qdrant embedding storage (embedding_service)
- [x] LangGraph multi-agent pipelines (state, graph, agents)

## Phase 3: Dashboard & Workers (Completed)
- [x] Asynchronous tasks (indexing, pr_pipeline)
- [x] Real-time updates WebSocket connections

## Phase 4: Refined Frontend (Completed)
- [x] Next.js 16 TypeScript setup
- [x] Secure HTTP-only refresh cookie flow (FastAPI callbacks + Axios interceptor)
- [x] Modular api clients layout (`lib/api/`)
- [x] Developer-first dashboard pages (page, login, callback, repositories, pull-requests, monitoring, search)
- [x] Clustered React Flow dependency views representation
- [x] Generated tests commit workflows
- [x] Risk score breakdowns details
- [x] Real-time PR Timeline mapping

## Phase 5: Monitoring (Completed)
- [x] Prometheus latency metrics hook
- [x] Pre-configured Grafana dashboard template (testpilot.json)

## Phase 6: Continuous Delivery & Live Verification (Completed)
- [x] Docker Compose live containers brought up and validated healthy
- [x] Fixed pydantic-settings JSON array origins decoding bug
- [x] Resolved circular import between models and base database registry
- [x] Switched from Poetry to fast pip build in backend Dockerfile
- [x] GitHub Actions CD workflow (`cd.yml`) to build and push images to GHCR on push to main
- [x] Live GitHub App webhook integration configuration guide (`GITHUB_APP_SETUP.md`)

## Release v1.1.0: Multi-VCS Integration & Upfront Validation (Completed)
- [x] Multi-VCS provider architecture adapters (GitHub, Bitbucket, GitLab, Azure DevOps, Custom Git)
- [x] Bitbucket 1-Click OAuth 2.0 & Personal Access Token (PAT) / App Password authentication
- [x] Token HTTPS clone URL injection (`x-access-token`, `x-token-auth`, `oauth2`, `Basic base64`)
- [x] Non-interactive Git safety (`GIT_TERMINAL_PROMPT="0"`, `GIT_ASKPASS="echo"`) & default branch fallback
- [x] Upfront REST API validation (HTTP 400 rejection for 404/401 non-existent repos)

## Release v1.2.0: Secured Multi-VCS Webhooks, Parallel LangGraph & AST Context Pruning (Completed)
- [x] `WebhookAdapter` protocol architecture (GitHub HMAC, Bitbucket HMAC, GitLab secret token, Azure DevOps secret token)
- [x] Provider-normalized `NormalizedPREvent` DTO (actions: `opened`, `synchronize`, `reopened`, `closed`)
- [x] Decoupled `IdempotencyService` infrastructure layer using Redis `webhook:{provider}:{repository}:{delivery_id}`
- [x] Unified router endpoint `POST /api/v1/webhooks/{provider}` returning `HTTP 202 Accepted` (`p95 < 200ms`)
- [x] Monorepo `PackageScope` boundary detector (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`)
- [x] Parallel LangGraph sub-graph fan-out (`impact_agent`, `search_agent`, `test_discovery_agent` concurrent branches)
- [x] Isolated state branch key ownership in `AgentState` eliminating state collisions
- [x] Priority AST context pruner achieving 32.2% token reduction
- [x] True wall-clock `total_pr_analysis_latency_ms` and EvalOps dashboard telemetry metrics
- [x] 5/5 Pytest unit tests, 16/16 Full System Integration tests, 6/6 Feature tests passed

## Version 2.0.0 Architecture Roadmap (Planned — To Be Done Later)
- [ ] Docker sandbox container runner migration from host subprocess calls (`execution_agent.py`)
- [ ] Automated Pull Request Auto-Remediation and autonomous fix branch commits
- [ ] Enterprise RBAC, SAML/SSO integration, and SOC2 audit compliance logging
