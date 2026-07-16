# TestPilot AI — Setup & Configuration

This guide provides steps for setting up and running TestPilot AI in your local environment.

## Environment Variables (`.env`)

Create a `.env` file in the project root:

```env
# Common
APP_ENV=dev
DEBUG=True

# Postgres
POSTGRES_DB=testpilot
POSTGRES_USER=testpilot
POSTGRES_PASSWORD=testpilot_secret
DATABASE_URL=postgresql+asyncpg://testpilot:testpilot_secret@postgres:5432/testpilot

# Redis
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# GitHub App Configuration (Placeholders for dev)
GITHUB_APP_ID=123456
GITHUB_CLIENT_ID=lv12345
GITHUB_CLIENT_SECRET=github_secret_placeholder
GITHUB_WEBHOOK_SECRET=webhook_secret_placeholder
GITHUB_APP_PRIVATE_KEY_PATH=/app/private-key.pem

# OpenAI / LLM Configurations
OPENAI_API_KEY=sk-placeholder
LITELLM_DEFAULT_MODEL=gpt-4o-mini
```

## Running the Platform

To spin up all services:

```bash
docker compose up -d --build
```

To run DB migrations:

```bash
docker compose exec backend alembic upgrade head
```

To stop all services:

```bash
docker compose down
```
