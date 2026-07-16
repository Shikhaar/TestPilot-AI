# ✈️ TestPilot AI

[![CD Build Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/cd.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![CI Check Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Shikhaar/TestPilot-AI/pulls)

> **AI-Powered Regression Testing Platform for Modern Software Engineering Teams**

TestPilot AI is a production-grade AI platform that automatically analyzes GitHub Pull Requests, maps codebase impact trees, discovers existing test structures, writes missing tests using LLMs, and posts code reviews back to GitHub.

---

## 🏗️ System Architecture

```
                    ┌───────────────────────────┐
                    │      Next.js Frontend     │
                    │   (React + Tailwind)      │
                    └─────────────┬─────────────┘
                                  │ REST / WebSockets / SSE
                                  │
                    ┌─────────────▼─────────────┐
                    │      FastAPI Backend      │
                    │  (Python 3.12 / Alembic)  │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
   ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
   │ PostgreSQL  │         │    Redis    │         │   Qdrant    │
   │ (Relational)│         │ (Celery/WS) │         │ (Vector DB) │
   └─────────────┘         └─────────────┘         └─────────────┘
```

The core engine uses a state-of-the-art **multi-agent orchestration workflow** powered by **LangGraph**, consisting of 11 specialized agent nodes:

1. **Planner Agent**: Orchestrates the pipeline entry and validates input parameters.
2. **Diff Agent**: Parses the Git diff and extracts modified AST symbols (functions, classes, variables).
3. **Dependency Agent**: Computes the dependency imports graph for affected symbols.
4. **Impact Agent**: Graph-traverses imported models/APIs to map regression scope.
5. **Search Agent**: Queries semantic embeddings in Qdrant to find contextually relevant codebase samples.
6. **Test Discovery Agent**: Discovers and indexes existing test structures.
7. **Test Generator Agent**: Synthesizes custom PyTest test code to cover modified blocks.
8. **Execution Agent**: Executes test suites in insulated subprocesses.
9. **Failure Analysis Agent**: Explains test failures with actionable code patches.
10. **Review Agent**: Compiles code changes, quality risk metrics, and generated tests into a markdown review.
11. **Documentation Agent**: Identifies missing API docs and creates updates matching the code changes.

---

## 🛠️ Technology Stack

* **Frontend**: Next.js 15 (React 19, TailwindCSS, CSS Variables)
* **Backend**: FastAPI, SQLAlchemy 2, Alembic, Poetry
* **Agent Flow & Orchestration**: LangGraph, LiteLLM, Instructor, Sentence-Transformers
* **Background Tasks**: Celery, Redis, Kombu
* **Vector Storage**: Qdrant Vector DB
* **Observability & Infrastructure**: Docker, Docker Compose, Nginx, Prometheus, Grafana, OpenTelemetry

---

## 🚀 Getting Started

### Prerequisites

* **Docker & Docker Compose** (WSL2 backend enabled if running on Windows)
* **Node.js v18+** (for local frontend hacking)
* **Python 3.12** (for local backend hacking)

### Configuration (`.env`)

Clone the template and configure your API tokens:
```bash
cp .env.example .env
```

Ensure the following variables are set in `.env`:
* `OPENAI_API_KEY`: Your OpenAI/LLM provider API key (processed via LiteLLM).
* `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: For GitHub OAuth integration.
* `GITHUB_APP_ID` / `GITHUB_APP_PRIVATE_KEY_PATH`: For GitHub App webhook events.

---

## 💻 CLI Developer Commands (Makefile)

A `Makefile` is provided with helpful shortcuts for local execution:

### Infrastructure
```bash
make dev             # Start all services (Frontend, Backend, DB, Redis, Grafana)
make stop            # Shut down all running services
make rebuild         # Rebuild all Docker images from scratch and restart
make logs            # Tail docker container logs
```

### Database & Migrations
```bash
make migrate         # Apply pending Alembic database migrations
make db-shell        # Open PostgreSQL client interface (psql)
make db-reset        # Wipe and recreate database tables
```

### Quality Assurance & Linting
```bash
make lint            # Check files using Ruff linter
make lint-fix        # Auto-fix Ruff formatting/import rules
make format          # Format Python codebase using Black
```

### Running Tests
```bash
make test            # Execute Python test suite
make test-cov        # Run tests and output HTML coverage reports
```

---

## 📊 Monitoring & Port Mappings

Once running (`make dev`), you can access different platform dashboards:

| Service | Address | Description |
| :--- | :--- | :--- |
| **Web Dashboard** | [http://localhost:3000](http://localhost:3000) | Frontend interface (Metrics, PRs, Repositories). |
| **Backend API** | [http://localhost:8000/docs](http://localhost:8000/docs) | FastAPI interactive Swagger documentation. |
| **Qdrant Console** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | Semantic Vector database admin UI. |
| **Celery Flower** | [http://localhost:5555](http://localhost:5555) | Asynchronous task queues and workers metrics. |
| **Grafana** | [http://localhost:3001](http://localhost:3001) | Promethus logs and system health telemetry. |

---

## 🛡️ License

Distributed under the **MIT License**. See `LICENSE` for more information.
