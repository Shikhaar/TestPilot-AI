# TestPilot AI — Task List (V2)

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
- [x] Next.js 15 TypeScript setup
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
- [x] Switched from Poetry to fast pip build in backend Dockerfile (reduced CUDA GPU build dependencies)
- [x] GitHub Actions CD workflow (`cd.yml`) to build and push images to GHCR on push to main
- [x] Live GitHub App webhook integration configuration guide (`GITHUB_APP_SETUP.md`)

## Phase 7: Multi-VCS Provider & EvalOps Quality Telemetry Platform (Completed — Release v1.1.0)
- [x] Multi-VCS provider architecture adapters (GitHub, Bitbucket, GitLab, Azure DevOps, Custom Git)
- [x] Bitbucket 1-Click OAuth 2.0 & Personal Access Token (PAT) / App Password authentication
- [x] Token HTTPS clone URL injection (`x-access-token`, `x-token-auth`, `oauth2`, `Basic base64`)
- [x] Non-interactive Git safety (`GIT_TERMINAL_PROMPT="0"`, `GIT_ASKPASS="echo"`) & default branch fallback
- [x] Upfront REST API validation (HTTP 400 rejection for 404/401 non-existent repos)
- [x] 4-Category EvalOps telemetry collector (`GET /api/v1/evalops/metrics`)
- [x] Live EvalOps monitoring dashboard (`/monitoring`) with time-series trends and quality gauges
- [x] 1-Click Dev Authentication (`POST /api/v1/auth/dev-login`)
- [x] Startup database lifespan migration for `provider` and `provider_repo_id` columns
- [x] SQLite local dev fallback & FastAPI `background_tasks` Celery fallback
- [x] Created `docs/features/VCS_PROVIDERS.md` and `docs/features/EVALOPS_AND_TELEMETRY.md`
- [x] 16/16 Full System Integration Tests passed & released as `v1.1.0` on `main`

## Phase 8: Version 2.0.0 Architecture Roadmap (Planned)
- [ ] Multi-Package AST Graph Resolution for monorepos (npm workspaces, Lerna, Nx, Cargo, Go)
- [ ] Enterprise Webhook Receiver for Bitbucket, GitLab, and Azure DevOps pull requests
- [ ] Sandboxed Ephemeral Docker / WebAssembly Test Execution Runner
- [ ] Automated Pull Request Auto-Remediation and auto-fix branch commits
- [ ] LangGraph parallel sub-graphs and dynamic context window pruning (40% latency reduction)
- [ ] Fine-Tuned Local LLM integration (DeepSeek-Coder, CodeLlama, Qwen-Coder via Ollama/vLLM)
- [ ] Enterprise RBAC, SAML/SSO integration, and SOC2 audit logging


