# TestPilot AI — Developer Setup Guide

This guide covers all options for running TestPilot AI locally, including environment configuration, service endpoints, and Makefile automation.

---

## Option 1: 60-Second Containerized Deployment (Recommended)

```bash
git clone https://github.com/Shikhaar/TestPilot-AI.git
cd TestPilot-AI
cp .env.example .env
docker compose up -d
docker compose exec backend alembic upgrade head
```

Open `http://localhost:3000`.

---

## Option 2: Native Host Development Setup

### Prerequisites

- Python 3.12 & Poetry
- Node.js v18+ & npm
- Docker & Docker Compose (for PostgreSQL, Redis, and Qdrant)

### 1. Start Infrastructure Services

```bash
docker compose up -d postgres redis qdrant
```

### 2. Configure Host Connection Strings (`.env`)

When running the backend natively, replace the Docker service hostnames (`postgres`, `redis`, `qdrant`) with `localhost`. All other values stay the same as `.env.example`.

```env
# Application
APP_NAME=TestPilot AI
APP_ENV=development
DEBUG=true
SECRET_KEY=change-me-to-a-very-long-random-secret-key-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80

# PostgreSQL (use localhost instead of Docker service name)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=testpilot
POSTGRES_PASSWORD=testpilot_secret
POSTGRES_DB=testpilot
DATABASE_URL=postgresql+asyncpg://testpilot:testpilot_secret@localhost:5432/testpilot

# Redis (use localhost instead of Docker service name)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_secret
REDIS_URL=redis://:redis_secret@localhost:6379/0
CELERY_BROKER_URL=redis://:redis_secret@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:redis_secret@localhost:6379/1

# Qdrant (use localhost instead of Docker service name)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=qdrant_secret
QDRANT_URL=http://localhost:6333

# GitHub App
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY_PATH=/secrets/github-private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_APP_NAME=testpilot-ai-app

# JWT Authentication
JWT_SECRET_KEY=change-me-to-another-long-random-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# LiteLLM / OpenAI
OPENAI_API_KEY=sk-placeholder-replace-with-real-key
LITELLM_DEFAULT_MODEL=gpt-4o-mini
LITELLM_FALLBACK_MODEL=ollama/mistral
USE_LOCAL_EMBEDDINGS=true
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=TestPilot AI
```

### 3. Start Backend API

```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --port 8000 --reload
```

### 4. Start Frontend Client

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Service Endpoints

| Service | Endpoint | Purpose |
| :--- | :--- | :--- |
| **Web Interface** | `http://localhost:3000` | Application frontend dashboard |
| **Backend Swagger API** | `http://localhost:8000/docs` | Interactive OpenAPI specification |
| **Qdrant Vector Dashboard** | `http://localhost:6333/dashboard` | Vector storage collection manager |
| **Celery Flower** | `http://localhost:5555` | Distributed task execution monitor |
| **Grafana Dashboard** | `http://localhost:3001` | Prometheus telemetry visualization |

---

## Makefile Automation

| Command | Action |
| :--- | :--- |
| `make dev` | Launch complete stack via Docker Compose |
| `make stop` | Terminate all active container services |
| `make migrate` | Execute pending Alembic migrations |
| `make db-reset` | Reset database state and re-apply schema |
| `make lint` | Run Ruff static analysis across Python modules |
| `make test` | Execute Pytest automated test suite |

---

## Usage Workflow

1. **Access the Dashboard** at `http://localhost:3000`.
2. **Connect a Repository** — select from your linked GitHub account or enter any public repository URL.
3. **Observe AST Indexing** — track real-time AST parsing progress, health scores, and coverage metrics.
4. **Code Search & Unit Testing** — execute 3-layer hybrid code searches or generate automated unit test suites.
5. **Disconnect a Repository** — purge storage directories and Qdrant vector collections with one click.
