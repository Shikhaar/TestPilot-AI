# ✈️ TestPilot AI

> AI-Powered Regression Testing Platform for Modern Software Engineering Teams

TestPilot AI is a production-grade AI platform that automatically analyzes GitHub Pull Requests, understands codebase impact, discovers and runs regression suites, writes missing tests using LLMs (LiteLLM + Instructor), and posts smart code reviews back to GitHub.

---

## 🏗️ Architecture

```
                  ┌───────────────────────────┐
                  │      Next.js Frontend     │
                  │   (React + Tailwind)      │
                  └─────────────┬─────────────┘
                                │ REST/WebSocket/SSE
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

The system employs a multi-agent workflow powered by **LangGraph** with 11 specialized agent nodes:

1. **Planner Agent**: Pipeline entry and pre-condition validation.
2. **Diff Agent**: Parses the Git diff and extracts modified AST symbols.
3. **Dependency Agent**: Queries file-level and function-level imports.
4. **Impact Agent**: Graph-traverses dependencies to find affected APIs/routes.
5. **Search Agent**: Performs hybrid semantic search via Qdrant.
6. **Test Discovery Agent**: Categorizes existing test files.
7. **Test Generator Agent**: Synthesizes custom tests targeting code gaps.
8. **Execution Agent**: Runs regression test suites in a subprocess.
9. **Failure Analysis Agent**: Explains test failures with suggested fixes.
10. **Review Agent**: Formulates a complete, structured GitHub review.
11. **Documentation Agent**: Suggests doc updates for modified API routes.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
* **Asynchronous Tasks**: Celery, Redis, Kombu
* **AI & Embeddings**: LangGraph, LiteLLM, Instructor, Sentence Transformers
* **Vector Store**: Qdrant
* **Frontend**: Next.js 15 (React 19, TailwindCSS)
* **DevOps**: Docker, Docker Compose, Nginx, Prometheus, Grafana, OpenTelemetry

---

## 🚀 Getting Started

### Prerequisites

* Docker and Docker Compose
* Node.js (v18+)
* Python 3.12 (if running backend outside Docker)

### Run with Docker Compose

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Build and spin up the architecture:
   ```bash
   make dev
   ```
3. Run migrations:
   ```bash
   make migrate
   ```

Now visit:
* Dashboard: http://localhost:3000
* Backend API: http://localhost:8000/docs
* Prometheus Metrics: http://localhost:8000/metrics
* Celery Flower: http://localhost:5555
