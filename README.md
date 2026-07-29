# TestPilot AI

[![CD Build Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/cd.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![CI Check Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Shikhaar/TestPilot-AI/pulls)

**Automated Regression Testing & Tree-Sitter AST Code Indexing Platform**

TestPilot AI is an enterprise-grade AI software engineering platform designed to automate regression analysis, map codebase dependency impact trees, discover existing test structures, synthesize unit test suites using Large Language Models (LLMs), and automate Pull Request reviews on GitHub.

---

## Platform Overview

[TestPilot AI Dashboard](docs/images/dashboard.png)

> **Platform Overview** — Automated regression testing, vector AST indexing, and risk impact analysis dashboard showing repository health metrics, live AI agent telemetry, and quality token analytics.

---

## Executive Summary

Modern software engineering teams face significant friction verifying regression risks across complex, microservice-oriented codebases. TestPilot AI solves this by combining deterministic static analysis (Tree-sitter Abstract Syntax Trees) with non-deterministic artificial intelligence (LangGraph Multi-Agent Orchestration and Qdrant Vector Retrieval) to perform context-aware test generation and risk evaluation in CI/CD pipelines.

---

## Connected Repositories

[Connected Repositories]

> **Repository Management** — Connect GitHub repositories, track AST indexing progress, monitor health scores, and manage connected codebases from a unified view.

---

## System Architecture

[TestPilot AI Architecture Diagram]

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Next.js 16 Frontend                           │
│                        (React 19, TailwindCSS)                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST / WebSockets / SSE
┌────────────────────────────────────▼────────────────────────────────────┐
│                             FastAPI Backend                             │
│                      (Python 3.12, Async SQLAlchemy)                    │
└──────┬─────────────────────────────┬─────────────────────────────┬──────┘
       │                             │                             │
┌──────▼──────┐               ┌──────▼──────┐               ┌──────▼──────┐
│ PostgreSQL  │               │    Redis    │               │   Qdrant    │
│ (Relational)│               │ (Broker/WS) │               │ (Vector DB) │
└─────────────┘               └──────┬──────┘               └─────────────┘
                                     │
                              ┌──────▼──────┐
                              │Celery Worker│
                              │(LangGraph)  │
                              └─────────────┘
```

The core engine uses a stateful **multi-agent orchestration workflow** powered by **LangGraph**, consisting of 11 specialized agent nodes:

1. **Planner Agent**: Validates incoming pipeline requests and normalizes execution state.
2. **Diff Agent**: Parses unified Git diffs and maps changed line ranges to Tree-sitter AST nodes (functions, classes, routes).
3. **Dependency Agent**: Queries the static import graph to construct an upstream and downstream call graph.
4. **Impact Agent**: Performs graph traversal across imported models, services, and route handlers to calculate total blast radius.
5. **Search Agent**: Queries Qdrant vector embeddings to retrieve relevant reference code snippets via hybrid RAG.
6. **Test Discovery Agent**: Indexes existing test frameworks (PyTest, Vitest/Jest, JUnit, Go Test) and identifies coverage gaps.
7. **Test Generator Agent**: Synthesizes production-ready unit test files matching repository code style using LLM structured outputs.
8. **Execution Agent**: Runs generated test suites inside isolated subprocess environments to verify test validity.
9. **Failure Analysis Agent**: Parses stdout/stderr logs of failing tests and generates root-cause diagnostic reports.
10. **Review Agent**: Aggregates risk metrics, affected symbols, and generated code into structured Pull Request markdown comments.
11. **Documentation Agent**: Identifies API documentation drifts and generates OpenAPI/Markdown specification updates.

---

## Key Technical Features

### Multi-Language Tree-sitter AST Parsing
Supports deep AST parsing for TypeScript, JavaScript, Python, Go, Java, and Rust. Extracts function signatures, decorators, class hierarchies, imports, exports, and web route handlers (FastAPI, Express, Spring, Flask).

### Dynamic README & Description Extraction
Extracts repository documentation directly from local cloned file paths or fallbacks to GitHub REST API endpoints dynamically, avoiding stale or hardcoded fallback data.

### Real-Time Async Architecture
Built with FastAPI async endpoints, Redis Pub/Sub, and WebSockets to push live indexing progress, AST parsing metrics, and pipeline status updates directly to the Next.js frontend.

### One-Click GitHub Pull Request Creation
Provides automated branch creation and commit generation via the GitHub API, allowing developers to push generated unit tests directly to active Pull Requests.

### GitHub Linguist Language Detection
Automatically detects the primary programming language of each connected repository by querying the GitHub Linguist API, providing accurate language metadata without requiring manual configuration.

### Repository Disconnect & Storage Cleanup
Provides a one-click disconnect feature from the repository dashboard. Disconnecting a repository removes the database record, deletes the local cloned storage directory, and purges all associated AST vector embeddings from Qdrant — freeing up disk space and vector storage instantly.

---

## Technology Stack

* **Frontend**: Next.js 16, React 19, TailwindCSS, CSS Modules
* **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (AsyncIO), Alembic, Pydantic v2, Poetry
* **AI & Agent Orchestration**: LangGraph, Tree-sitter, LiteLLM, Instructor, Sentence-Transformers
* **Asynchronous Infrastructure**: Celery, Redis, Kombu
* **Vector Storage**: Qdrant Vector DB
* **Observability**: Prometheus, Grafana, OpenTelemetry, Celery Flower, Structlog

---

## Quickstart Guide

### Option 1: 60-Second Containerized Deployment (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/Shikhaar/TestPilot-AI.git
   cd TestPilot-AI
   ```

2. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```

3. Spin up all containerized services (Frontend, Backend, PostgreSQL, Redis, Qdrant, Celery, Grafana):
   ```bash
   docker compose up -d
   ```

4. Execute database migrations:
   ```bash
   docker compose exec backend poetry run alembic upgrade head
   ```

5. Access the Web Dashboard at `http://localhost:3000`.

---

### Option 2: Native Host Development Setup

#### Prerequisites
* Python 3.12 & Poetry
* Node.js v18+ & npm
* Docker & Docker Compose (for PostgreSQL, Redis, and Qdrant infrastructure)

#### 1. Start Storage Infrastructure
```bash
docker compose up -d postgres redis qdrant
```

#### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure host connection strings are configured for native execution:
```env
POSTGRES_HOST=localhost
REDIS_HOST=localhost
QDRANT_HOST=localhost
DATABASE_URL=postgresql+asyncpg://testpilot:testpilot_secret@localhost:5432/testpilot
REDIS_URL=redis://:redis_secret@localhost:6379/0
QDRANT_URL=http://localhost:6333
```

#### 3. Run Backend API
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --port 8005 --reload
```
FastAPI Swagger documentation will be available at `http://localhost:8005/docs`.

#### 4. Run Frontend Web App
```bash
cd frontend
npm install
npm run dev
```
Frontend interface will be available at `http://localhost:3000`.

---

## Usage Workflow

1. **Access the Dashboard**: Open `http://localhost:3000`.
2. **Connect a Repository**: Select a repository from your linked GitHub account or enter any public GitHub repository URL (e.g., `expressjs/express` or `psf/requests`).
3. **Observe AST Indexing**: Track progress as the backend clones the target repository, parses AST symbols, and computes health and coverage metrics.
4. **Generate Unit Tests**: Open the repository detail page, click **Generate Tests**, inspect the synthesized test file, and click **Create PR on GitHub** to push changes directly to the remote repository.
5. **Disconnect a Repository**: Click the **Disconnect** button on any repository card to remove it from TestPilot AI, free up local disk storage, and purge all associated vector embeddings.

---

## Infrastructure & Monitoring Endpoints

| Service | Endpoint | Purpose |
| :--- | :--- | :--- |
| **Web Interface** | `http://localhost:3000` | Application frontend dashboard |
| **Backend OpenAPI Docs** | `http://localhost:8005/docs` | Interactive Swagger API specification |
| **Qdrant Vector Console** | `http://localhost:6333/dashboard` | Vector storage & collection management |
| **Celery Flower** | `http://localhost:5555` | Worker queue and task execution monitor |
| **Grafana Telemetry** | `http://localhost:3001` | Prometheus metric visualization dashboard |

---

## Developer Automation Tools (Makefile)

| Command | Action |
| :--- | :--- |
| `make dev` | Launch complete stack via Docker Compose |
| `make stop` | Terminate all active container services |
| `make migrate` | Execute pending Alembic migrations |
| `make db-reset` | Reset database state and re-apply schema |
| `make lint` | Run Ruff static analysis across Python modules |
| `make test` | Execute Pytest automated test suite |

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
