# TestPilot AI

[![CD Build Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/cd.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![CI Check Status](https://github.com/Shikhaar/TestPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Shikhaar/TestPilot-AI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Shikhaar/TestPilot-AI/pulls)

**Automated Regression Testing & Tree-Sitter AST Code Indexing Platform**

TestPilot AI is an open-source AI software engineering platform designed to automate regression analysis, map codebase dependency impact trees, discover existing test structures, synthesize unit test suites using Large Language Models (LLMs), and automate Pull Request reviews on GitHub.

---

## Platform Overview

![TestPilot AI Dashboard](docs/images/dashboard.png)

> **Platform Overview** — Automated regression testing, vector AST indexing, and risk impact analysis dashboard showing repository health metrics, live AI agent telemetry, and quality token analytics.

---

## Executive Summary

Modern software engineering teams face significant friction verifying regression risks across complex, microservice-oriented codebases. TestPilot AI solves this by combining deterministic static analysis (Tree-sitter Abstract Syntax Trees) with non-deterministic artificial intelligence (LangGraph Multi-Agent Orchestration and Qdrant Vector Retrieval) to perform context-aware test generation and risk evaluation in CI/CD pipelines.

---

## Engineering & System Documentation

For technical recruiters, engineering leaders, and open-source contributors, comprehensive system specifications and feature deep-dives are organized in the [`docs/`](docs/) directory:

| Document | Description | Key Technical Concepts |
| :--- | :--- | :--- |
| [**System Architecture**](docs/architecture.md) | Decoupled platform topology & component interactions | Next.js 16, FastAPI, PostgreSQL, Qdrant, Celery |
| [**Project Overview**](docs/PROJECT_OVERVIEW.md) | Comprehensive platform overview & system capabilities | End-to-end PR review pipeline & AST impact mapping |
| [**Multi-VCS Provider Architecture**](docs/features/VCS_PROVIDERS.md) | Multi-VCS integration & authentication model | GitHub, Bitbucket, GitLab, Azure DevOps, PAT tokens |
| [**EvalOps Telemetry Engine**](docs/features/EVALOPS_AND_TELEMETRY.md) | Quality benchmarks, repair metrics & token analytics | Pass@1/Pass@N, repair success rate, token cost estimation |
| [**3-Layer Code Search Engine**](docs/features/CODE_SEARCH_AND_INDEXING.md) | Parallel multi-layer code retrieval architecture | Dense 384-dim vectors, PostgreSQL ILIKE, disk scanner |
| [**Test Generation & Verification**](docs/features/TEST_GENERATION_AND_VERIFICATION.md) | Multi-agent test synthesis & self-healing verification | Exit codes, pytest/jest JSON reports, self-healing loop |
| [**GitHub OAuth & Session Security**](docs/features/GITHUB_OAUTH_AND_SECURITY.md) | Enterprise authentication & security model | GitHub OAuth 2.0, JWT tokens, zero password storage |
| [**Monitoring & Telemetry**](docs/features/MONITORING_AND_TELEMETRY.md) | Queue monitoring & graceful fallback UI | Celery queue latency, Prometheus metrics, fallback banners |
| [**Developer Setup Guide**](docs/setup.md) | Containerized and local development guide | Docker Compose, environment variables, alembic migrations |
| [**Implementation Roadmap**](docs/plans/01_INITIAL_IMPLEMENTATION_PLAN.md) | Chronological development roadmap & milestone plans | Phase-by-phase implementation logs |

---

## System Architecture

```mermaid
graph TD
    Client[Next.js 16 Frontend Client] -->|REST / WebSockets| FastAPI[FastAPI Backend Server]
    
    FastAPI -->|Async Tasks| Redis[Redis Broker]
    Redis -->|Dispatch Jobs| Celery[Celery Task Worker]
    
    FastAPI -->|Query/Write| PG[(PostgreSQL Database)]
    Celery -->|Query/Write| PG
    
    FastAPI -->|3-Layer Search| Qdrant[(Qdrant Vector DB)]
    Celery -->|Upsert Chunks| Qdrant
    
    Celery -->|Execute Loop| LangGraph[LangGraph Agent Engine]
    LangGraph -->|Sandboxed Execution| Sandbox[Pytest / Jest Sandbox Runner]
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

## Tech Stack & Capabilities

* **Frontend**: Next.js 16, React 19, TailwindCSS, CSS Modules
* **Backend**: Python 3.12, FastAPI, Async SQLAlchemy 2, Alembic, Pydantic v2, Poetry
* **AI & Multi-Agent Engine**: LangGraph, Tree-sitter AST, LiteLLM, Instructor, Sentence-Transformers
* **Vector & Relational Storage**: Qdrant Vector DB (384-dim dense vectors), PostgreSQL 16
* **Async Infrastructure**: Celery 5, Redis 7 (Pub/Sub & Broker)
* **Observability & Monitoring**: Prometheus, Grafana, OpenTelemetry, Celery Flower

---

## Quickstart Guide

### Option 1: 60-Second Containerized Deployment (Recommended for New Users & Reviewers)

1. **Clone the repository**:
 ```bash
 git clone https://github.com/Shikhaar/TestPilot-AI.git
 cd TestPilot-AI
 ```

2. **Copy the environment configuration**:
 ```bash
 cp .env.example .env
 ```

3. **Spin up containerized services**:
 ```bash
 docker compose up -d
 ```

4. **Execute database migrations**:
 ```bash
 docker compose exec backend poetry run alembic upgrade head
 ```

5. **Access the Web Dashboard** at `http://localhost:3000`.

---

### Option 2: Native Host Development Setup (For Active Core Contributors)

<details>
<summary>Click to expand Native Host Setup instructions</summary>

#### Prerequisites
* Python 3.12 & Poetry
* Node.js v18+ & npm
* Docker & Docker Compose (for PostgreSQL, Redis, and Qdrant infrastructure)

#### 1. Start Infrastructure
```bash
docker compose up -d postgres redis qdrant
```

#### 2. Configure Host Connection Strings (`.env`)
```env
POSTGRES_HOST=localhost
REDIS_HOST=localhost
QDRANT_HOST=localhost
DATABASE_URL=postgresql+asyncpg://testpilot:testpilot_secret@localhost:5432/testpilot
REDIS_URL=redis://:redis_secret@localhost:6379/0
QDRANT_URL=http://localhost:6333
```

#### 3. Start Backend API
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --port 8000 --reload
```

#### 4. Start Frontend Client
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000`.

</details>

---

## Usage Workflow

1. **Access the Dashboard**: Open `http://localhost:3000`.
2. **Connect a Repository**: Select a repository from your linked GitHub account or enter any public GitHub repository URL.
3. **Observe AST Indexing**: Track real-time AST parsing progress, health scores, and coverage metrics.
4. **Code Search & Unit Testing**: Execute 3-layer hybrid code searches or generate automated unit test suites.
5. **Disconnect a Repository**: Purge storage directories and Qdrant vector collections with one click.

---

## Infrastructure & Endpoints

| Service | Endpoint | Purpose |
| :--- | :--- | :--- |
| **Web Interface** | `http://localhost:3000` | Application frontend dashboard |
| **Backend Swagger API** | `http://localhost:8000/docs` | Interactive OpenAPI specification |
| **Qdrant Vector Dashboard** | `http://localhost:6333/dashboard` | Vector storage collection manager |
| **Celery Flower** | `http://localhost:5555` | Distributed task execution monitor |
| **Grafana Dashboard** | `http://localhost:3001` | Prometheus telemetry visualization |

---

## Developer Automation (Makefile)

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

Distributed under the **MIT License**. See `LICENSE` for details.
