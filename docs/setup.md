# TestPilot AI — Setup & Configuration (Present State)

This guide details setting up and running TestPilot AI in your local environment using Docker Compose and Node.js.

---

## 1. Environment Configuration (`.env`)

Ensure `.env` in the root directory contains Docker container hostnames (`postgres`, `redis`, `qdrant`):

```env
# Common
APP_ENV=dev
DEBUG=True

# Database (Docker service name: postgres)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=testpilot
POSTGRES_USER=testpilot
POSTGRES_PASSWORD=testpilot_secret
DATABASE_URL=postgresql+asyncpg://testpilot:testpilot_secret@postgres:5432/testpilot

# Redis (Docker service name: redis)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Qdrant (Docker service name: qdrant)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_URL=http://qdrant:6333

# GitHub OAuth & App Configuration
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_APP_ID=123456
GITHUB_WEBHOOK_SECRET=webhook_secret_placeholder

# LLM & Embeddings
USE_LOCAL_EMBEDDINGS=true
LITELLM_DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-placeholder
```

---

## 2. Running Services with Docker Compose

To build and start all backend services (`backend`, `celery-worker`, `postgres`, `redis`, `qdrant`):

```bash
docker compose up -d --build
```

To view logs:
```bash
docker logs testpilot-backend -f
```

To run DB migrations:
```bash
docker compose exec backend alembic upgrade head
```

---

## 3. Running Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.
