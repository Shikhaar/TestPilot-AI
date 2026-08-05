# TestPilot AI — Implementation Plan

> **AI-Powered Regression Testing Platform for Modern Software Engineering Teams**

This document outlines the complete production-grade architecture and phased build plan for TestPilot AI.

---

## Overview

TestPilot AI is a distributed, AI-augmented engineering intelligence platform that hooks into GitHub Pull Request workflows to:

1. Parse and understand codebases via AST (Tree-sitter)
2. Build dependency/call/import graphs
3. Run impact analysis on PR diffs
4. Discover, generate, and execute tests
5. Analyze failures with AI root-cause explanations
6. Post structured GitHub Review Comments with risk scores
7. Learn from historical bugs to predict future regressions

---

## User Review Required

> [!IMPORTANT]
> **Scope Decision**: This plan covers the full system architecture. Given complexity, I recommend building in **4 phases** (see below). Please confirm:
> - Should I build all 4 phases in one session, or start with Phase 1 (Foundation + Backend Core) and proceed incrementally?
> - Do you have OpenAI API keys, GitHub OAuth App credentials, or Qdrant Cloud? Or should I use placeholder `.env` values?
> - Should the frontend be deployed alongside the backend, or built as a standalone Next.js app?

> [!WARNING]
> **GitHub OAuth & Webhooks**: The GitHub integration requires a registered GitHub App (not just OAuth). I'll scaffold the setup with placeholder secrets and provide a setup guide.

---

## Open Questions

> [!IMPORTANT]
> 1. **LLM Keys**: Do you have an OpenAI API key for GPT-4.1? Or should I configure LiteLLM to fall back to a local model?
> 2. **Qdrant**: Self-hosted via Docker Compose, or Qdrant Cloud?
> 3. **GitHub App**: Have you created one? I'll need: `APP_ID`, `PRIVATE_KEY`, `WEBHOOK_SECRET`, `CLIENT_ID`, `CLIENT_SECRET`.
> 4. **Deployment Target**: Local dev only, or should I include production Nginx + SSL config?
> 5. **Frontend First?**: Should I prioritize the Dashboard UI alongside the backend, or backend-first?

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub                               │
│  PR Opened → Webhook → GitHub App → PR Review          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS Webhook
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Nginx (Reverse Proxy)                  │
└────────────────────┬────────────────────────────────────┘
                     │
           ┌──────────┴──────────┐
           ▼                     ▼
 ┌──────────────────┐  ┌──────────────────────┐
 │  FastAPI Backend │  │  Next.js 15 Frontend │
 │  (Python 3.12)   │  │  (TypeScript)        │
 └────────┬─────────┘  └──────────────────────┘
          │
     ┌────┴─────────────────────────────────────┐
     │              Redis (Broker)              │
     └────┬─────────────────────────────────────┘
          │
     ┌────▼────────────────────────────────────┐
     │         Celery Workers                  │
     │  ┌─────────────────────────────────┐   │
     │  │     LangGraph Agent Pipeline    │   │
     │  │  Diff → Impact → TestGen →      │   │
     │  │  Execute → Analyze → Review     │   │
     │  └─────────────────────────────────┘   │
     └─────────────────────────────────────────┘
          │                   │
     ┌────▼────┐         ┌────▼────┐
     │PostgreSQL│        │ Qdrant  │
     │(primary) │        │(vectors)│
     └──────────┘        └─────────┘
          │
     ┌────▼──────────────────────┐
     │  Prometheus + Grafana     │
     │  OpenTelemetry Collector  │
     └───────────────────────────┘
```

---

## Proposed Changes

### Phase 1 — Project Scaffolding & Infrastructure

#### [NEW] Project Root
- `pyproject.toml` — Poetry config, all Python deps
- `docker-compose.yml` — All services: FastAPI, Celery, PostgreSQL, Redis, Qdrant, Prometheus, Grafana, Nginx
- `docker-compose.override.yml` — Local dev overrides
- `.env.example` — All env vars documented
- `Makefile` — Shortcuts: make dev, make test, make migrate, make lint
- `README.md` — Setup guide

#### [NEW] Backend: `backend/`
Clean Architecture layout:
```
backend/
├── app/
│   ├── api/                  # FastAPI routers
│   │   ├── v1/
│   │   │   ├── repositories.py
│   │   │   ├── pull_requests.py
│   │   │   ├── tests.py
│   │   │   ├── ai.py
│   │   │   ├── dashboard.py
│   │   │   └── webhooks.py
│   │   └── deps.py           # DI dependencies
│   ├── core/
│   │   ├── config.py         # Pydantic Settings
│   │   ├── security.py       # JWT + GitHub OAuth
│   │   ├── logging.py        # Structured logging
│   │   └── telemetry.py      # OpenTelemetry
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── repository.py
│   │   ├── pull_request.py
│   │   ├── test_run.py
│   │   ├── agent_run.py
│   │   └── ...
│   ├── schemas/              # Pydantic v2 schemas
│   ├── repositories/         # DB access layer
│   ├── services/             # Business logic
│   │   ├── github_service.py
│   │   ├── repository_indexer.py
│   │   ├── ast_parser.py
│   │   ├── dependency_graph.py
│   │   ├── impact_analyzer.py
│   │   ├── test_runner.py
│   │   └── risk_scorer.py
│   ├── agents/               # LangGraph agents
│   │   ├── graph.py          # LangGraph supervisor
│   │   ├── diff_agent.py
│   │   ├── dependency_agent.py
│   │   ├── impact_agent.py
│   │   ├── search_agent.py
│   │   ├── test_discovery_agent.py
│   │   ├── test_generator_agent.py
│   │   ├── execution_agent.py
│   │   ├── failure_analysis_agent.py
│   │   ├── review_agent.py
│   │   ├── documentation_agent.py
│   │   └── planner_agent.py
│   ├── tasks/                # Celery tasks
│   │   ├── pr_pipeline.py
│   │   ├── indexing.py
│   │   └── notifications.py
│   ├── workers/
│   │   └── celery_app.py
│   ├── database/
│   │   ├── base.py
│   │   └── session.py
│   ├── middleware/
│   │   ├── request_id.py
│   │   └── rate_limit.py
│   └── utils/
│       ├── git_utils.py
│       ├── tree_sitter_utils.py
│       └── qdrant_client.py
├── alembic/                  # DB migrations
├── tests/                    # Pytest suite
└── Dockerfile
```

#### [NEW] Frontend: `frontend/`
Next.js 15 + TypeScript + Tailwind + Shadcn:
```
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   ├── dashboard/
│   ├── repositories/
│   │   └── [id]/
│   ├── pull-requests/
│   │   └── [id]/
│   │       ├── review/
│   │       ├── coverage/
│   │       └── tests/
│   ├── dependency-graph/
│   └── settings/
├── components/
│   ├── ui/                   # Shadcn components
│   ├── dashboard/
│   ├── pr-review/
│   ├── dependency-graph/     # React Flow
│   ├── code-viewer/          # Monaco Editor
│   └── charts/
├── lib/
│   ├── api.ts                # React Query hooks
│   └── auth.ts
└── Dockerfile
```

#### [NEW] Infrastructure: `infra/`
```
infra/
├── nginx/
│   └── nginx.conf
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   └── dashboards/
└── otel/
    └── otel-collector.yml
```

#### [NEW] CI/CD: `.github/workflows/`
```
.github/
└── workflows/
    ├── ci.yml        # lint, test, security scan
    ├── docker.yml    # build & push images
    └── deploy.yml    # deploy to production
```

---

### Phase 2 — Core Backend Systems

**Key services to implement:**

| Service | Responsibility |
|---|---|
| `GithubService` | Webhook verification, PR data extraction, posting reviews |
| `RepositoryIndexer` | Clone repo, walk files, invoke AST parser, store chunks |
| `ASTParser` | Tree-sitter: extract functions, classes, imports, routes |
| `DependencyGraphBuilder` | Build directed graph from imports/calls using networkx |
| `ImpactAnalyzer` | Walk dependency graph from changed nodes, find affected tests |
| `TestDiscovery` | Regex + AST scan for pytest/jest/junit test files |
| `TestRunner` | Subprocess: pytest --json-report, jest --json, etc. |
| `RiskScorer` | Rule-based + LLM scoring of PR risk level |

---

### Phase 3 — LangGraph Multi-Agent Pipeline

**Agent State Schema** (typed TypedDict):
```python
class AgentState(TypedDict):
    pr_id: str
    repo_id: str
    diff: GitDiff
    changed_nodes: list[CodeNode]
    dependency_graph: nx.DiGraph
    affected_modules: list[str]
    existing_tests: list[TestFile]
    generated_tests: list[GeneratedTest]
    execution_results: TestRunResult
    failures: list[FailureAnalysis]
    review_comment: PRReview
    risk_score: RiskScore
    errors: list[str]
    retry_count: int
```

**LangGraph Flow:**
```
START
  → PlannerAgent (decides which agents to invoke)
  → DiffAgent (parse PR diff → changed_nodes)
  → DependencyAgent (load/build dependency graph)
  → ImpactAgent (traverse graph → affected_modules)
  → SearchAgent (semantic + structural code retrieval)
  → TestDiscoveryAgent (find existing tests)
  → TestGeneratorAgent (GPT-4.1 → new tests, style-aware)
  → ExecutionAgent (run tests, collect results)
  → FailureAnalysisAgent (root cause, suggested fix)
  → ReviewAgent (write structured GitHub review)
  → DocumentationAgent (optional: update docs)
END
```

Each agent has:
- Structured output via `instructor`
- Retry logic with exponential backoff
- Per-agent logging to `agent_runs` table
- Tool bindings (search, AST query, subprocess)

---

### Phase 4 — Historical Learning & Risk Intelligence

**Learning from Historical Bugs:**
- Every merged PR, failed test run, and production incident is stored
- Embeddings of bug-related code changes stored in Qdrant
- When new PR arrives: similarity search against historical bugs
- `HistoricalRiskAgent` enriches review with: *"Similar change caused bug in commit abc123"*

**Risk Factors:**
- Auth/Payment/DB migration paths → HIGH baseline risk
- Coverage delta below threshold → escalate
- Historical regression rate of module → weighted risk
- Cyclomatic complexity increase → flag
- Public API surface changes → flag

---

## Database Schema

### PostgreSQL Tables

| Table | Key Columns |
|---|---|
| `users` | id, github_id, username, email, avatar_url, role |
| `repositories` | id, owner, name, full_name, clone_url, indexed_at, health_score |
| `pull_requests` | id, repo_id, pr_number, title, state, risk_score, coverage_delta |
| `commits` | id, repo_id, sha, message, author, timestamp |
| `repository_files` | id, repo_id, path, language, ast_hash, last_parsed |
| `dependency_graph` | id, repo_id, source_node, target_node, edge_type |
| `generated_tests` | id, pr_id, file_path, content, language, test_type, status |
| `test_runs` | id, pr_id, runner, status, started_at, finished_at, coverage |
| `test_results` | id, run_id, test_name, status, duration, failure_message |
| `review_comments` | id, pr_id, github_comment_id, body, risk_level, posted_at |
| `ai_logs` | id, agent_name, prompt_tokens, completion_tokens, latency_ms |
| `agent_runs` | id, pr_id, agent_name, status, input, output, duration_ms |
| `bug_history` | id, repo_id, commit_sha, module_path, bug_type, embedding_id |

### Qdrant Collections

| Collection | Stored |
|---|---|
| `repository_chunks` | File-level code chunks with metadata |
| `functions` | Function embeddings (name, body, file, language) |
| `classes` | Class/interface embeddings |
| `tests` | Test embeddings for similarity matching |
| `bug_history` | Bug-related code change embeddings |
| `pr_reviews` | Past review summaries for learning |

---

## API Surface

### Repositories
- `POST /api/v1/repositories/connect` — Add GitHub repo
- `POST /api/v1/repositories/{id}/index` — Trigger full indexing
- `GET /api/v1/repositories` — List repositories
- `GET /api/v1/repositories/{id}` — Repository detail + health

### Pull Requests
- `POST /api/v1/pr/analyze` — Trigger PR analysis pipeline
- `POST /api/v1/pr/review` — Post review to GitHub
- `GET /api/v1/pr/history` — PR history with risk scores

### Tests
- `POST /api/v1/tests/discover` — Discover existing tests
- `POST /api/v1/tests/generate` — Generate missing tests
- `POST /api/v1/tests/run` — Execute test suite
- `GET /api/v1/tests/results/{run_id}` — Test results

### AI
- `POST /api/v1/ai/chat` — Interactive chat with codebase
- `POST /api/v1/ai/search` — Semantic code search
- `POST /api/v1/ai/impact-analysis` — Manual impact analysis
- `POST /api/v1/ai/risk-score` — Risk scoring for a PR

### Webhooks
- `POST /api/v1/webhooks/github` — GitHub webhook receiver

### Dashboard
- `GET /api/v1/dashboard` — Aggregated metrics
- `GET /api/v1/metrics` — Prometheus-compatible metrics

---

## Verification Plan

### Automated Tests
```bash
# Backend unit + integration tests
cd backend && poetry run pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend && npm run test

# Lint
cd backend && poetry run ruff check . && poetry run mypy app/

# Docker build validation
docker compose build
```

### Manual Verification
1. `docker compose up` → all services healthy
2. Register a GitHub App → configure `.env`
3. Open a test PR → webhook fires → pipeline runs
4. Dashboard shows PR with risk score, generated tests, review comment
5. Check Grafana at `localhost:3001` for metrics

---

## Build Order (Phases)

| Phase | Scope | Estimated Files | Status |
|---|---|---|---|
| **Phase 1** | Scaffolding: Docker, Poetry, project structure, .env, Makefile | ~30 files | Completed |
| **Phase 2** | Backend core: models, schemas, services, basic API routes | ~60 files | Completed |
| **Phase 3** | LangGraph agents, Celery pipeline, webhook handling | ~40 files | Completed |
| **Phase 4** | Frontend (Next.js), historical learning, monitoring | ~50 files | Scaffolded |

**Total: ~180 production files**

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| ORM | SQLAlchemy 2 async | Full async, type-safe |
| Task Queue | Celery + Redis | Battle-tested, Flower for monitoring |
| Vector Store | Qdrant (self-hosted) | Open-source, fast, rich filtering |
| Graph Library | NetworkX | Proven for dependency graph traversal |
| AST | Tree-sitter | Multi-language, fast, accurate |
| Agent Framework | LangGraph | State-machine agents, not a simple chain |
| Schema Validation | Pydantic v2 + Instructor | Structured LLM output |
| Observability | OpenTelemetry + Prometheus + Grafana | Industry standard |
| Code Style | Black + Ruff + Mypy | Strict, automated |
