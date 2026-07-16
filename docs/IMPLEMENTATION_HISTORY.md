# TestPilot AI — Phase 1 Implementation History

This document records all components developed and verified during **Phase 1 (Backend Foundation & Scaffolding)**.

---

## 🛠️ Components Developed

### 1. Database & ORM Layer (`backend/app/models/`)
* **ORM Tables**:
  * `base.py`: Declares Base with custom mixins (`TimestampMixin`, `UUIDMixin`).
  * `user.py`: Holds user accounts, GitHub profiles, and tokens.
  * `repository.py`: Holds connected code repositories and indexing status.
  * `pull_request.py`: Holds pull request analysis status, files changed, and risk levels.
  * `commit.py`: Tracks commits pushed.
  * `repository_file.py`: Records AST-parsed code structures (functions, classes, routes) per file.
  * `dependency_graph.py`: Maps directed file-to-file import dependencies.
  * `generated_test.py`: Houses AI-generated test files and execution records.
  * `test_run.py` & `test_result.py`: Audits regression execution status and root causes.
  * `review_comment.py`: Stores finalized code review comment text.
  * `ai_log.py`: Audits LLM prompt/completion tokens, costs, and request latencies.
  * `agent_run.py`: Audits individual LangGraph agent runtime steps, retries, and errors.
  * `bug_history.py`: Stores historical regressions with Qdrant vector references.
* **Database Repositories (`backend/app/repositories/`)**:
  * `base.py`: Generic CRUD class (`get_by_id`, `get_all`, `create`, `update`, `delete`, `bulk_create`).
  * `user_repository.py`: Profile lookup by github ID, username, or email.
  * `repository_repo.py`: Connected repository query helpers.
  * `pull_request_repo.py`: PR lookups.
  * `test_run_repo.py`: PR test run history lookup.
* **Database Configuration**:
  * Configured `session.py` for fully asynchronous SQLAlchemy database engine and sessions.
  * Initialized Alembic migration environment: configured `alembic.ini`, `alembic/env.py` (configured with `asyncpg` and imports of all models), and `alembic/script.py.mako`.

### 2. Pydantic Schemas (`backend/app/schemas/`)
* `common.py`: Standard API wrappers, pagination envelopes, error payloads, health structures.
* `user.py`: Authentication profile mappings and OAuth refresh parameters.
* `repository.py`: Fields for repo connections, index stages, and health scores.
* `pull_request.py`: Structures for risk levels, changed files, impact maps, review comment details.
* `test.py`: Specifications for test runs, framework selections, and coverage results.
* `ai.py`: Schema definitions for semantic search and codebase chat conversations.
* `agent.py`: Monitored statistics for agent runs and pipeline steps.

### 3. Business Services (`backend/app/services/`)
* `github_service.py`: Decoupled service managing GitHub App token auth, PR file streams, diff summaries, check runs, and reviews.
* `ast_parser.py`: Multi-language syntax parser using Tree-sitter (for Python, JS, TS, Java, Go). Extracts functions, classes, imports, routes, and exports.
* `dependency_graph_builder.py`: Constructs directed dependency structures, computes BFS/DFS traversals for impact radius, and finds associated tests.
* `repository_indexer.py`: Indexing orchestrator.
* `impact_analyzer.py`: Downstream change blast radius traverser.
* `test_runner.py`: Test runner execution wrapper.
* `test_discovery.py`: Scan and list test cases.
* `risk_scorer.py`: Calculates PR risk ratings based on file counts, churn, and high-risk file impacts.
* `embedding_service.py`: Provides vector embeddings using lazy-loaded local `SentenceTransformers` or cloud LiteLLM models.

### 4. LangGraph Multi-Agent Engine (`backend/app/agents/`)
* `state.py`: Shared TypedDict state (`AgentState`) carrying pipeline states.
* `graph.py`: Orchestrates multi-agent routing.
* Fully scaffolded 11 agent nodes: `planner_agent.py`, `diff_agent.py`, `dependency_agent.py`, `impact_agent.py`, `search_agent.py`, `test_discovery_agent.py`, `test_generator_agent.py`, `execution_agent.py`, `failure_analysis_agent.py`, `review_agent.py`, `documentation_agent.py`.

### 5. Celery Asynchronous Workers (`backend/app/tasks/` & `workers/`)
* `celery_app.py`: Task queues (`pr_pipeline`, `indexing`, `notifications`) broker settings.
* `pr_pipeline.py` & `indexing.py`: Asynchronous background task workers.

### 6. API Routing, Middlewares, and Utilities
* Configured v1 REST endpoints inside `backend/app/api/v1/` for auth, repositories, PRs, tests, chat, search, webhooks, and dashboard.
* **WebSocket Streams (`backend/app/api/websocket.py`)**: Progress streams for PR analysis and indexing updates.
* **Middlewares (`backend/app/middleware/`)**:
  * `request_id.py`: Correlates log transactions.
  * `rate_limit.py`: Sliding window rate limiter.
* **Qdrant Client (`backend/app/utils/qdrant_client.py`)**: Collection management tools.

### 7. Test Suite (`backend/tests/`)
* `conftest.py`: Database mocks and testing fixtures.
* `test_api/test_repositories.py`: Asserts API repo listings.
* `test_api/test_webhooks.py`: Validates webhook delivery.
* `test_services/test_github_service.py` & `test_services/test_ast_parser.py`: Asserts parser and service functions.

### 8. Frontend Next.js Scaffold (`frontend/`)
* Scaffolded Next.js 15 app inside the `frontend/` workspace subdirectory configured with TypeScript, Tailwind CSS, and App Router.

### 9. DevOps & Config Setup
* `docker-compose.yml` & `docker-compose.override.yml`: Full orchestration stack.
* `infra/nginx/nginx.conf`: Nginx reverse-proxy setup.
* `.github/workflows/ci.yml`: GitHub Actions workflows.
