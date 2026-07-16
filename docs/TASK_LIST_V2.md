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

