# ==============================================================================
# TestPilot AI — Makefile
# Developer shortcuts for common tasks
# Usage: make <target>
# ==============================================================================

.PHONY: help dev stop build rebuild logs migrate migrate-create \
        test test-backend test-cov lint format typecheck \
        shell db-shell redis-cli qdrant-ui flower \
        clean clean-volumes index-all

DOCKER_COMPOSE = docker compose
BACKEND = $(DOCKER_COMPOSE) exec backend
PYTHON  = $(BACKEND) python
POETRY  = $(BACKEND) poetry run

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Infrastructure
# ==============================================================================

dev: ## Start all services in development mode
	@echo "🚀 Starting TestPilot AI..."
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo "✅ Services started. Dashboard: http://localhost:3000"
	@echo "📖 API Docs: http://localhost:8000/docs"
	@echo "🌸 Flower: http://localhost:5555"
	@echo "📊 Grafana: http://localhost:3001"

stop: ## Stop all services
	$(DOCKER_COMPOSE) down

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

rebuild: ## Rebuild and restart all services
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d

logs: ## Follow logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Follow backend logs only
	$(DOCKER_COMPOSE) logs -f backend

logs-worker: ## Follow Celery worker logs
	$(DOCKER_COMPOSE) logs -f celery-worker

# ==============================================================================
# Database
# ==============================================================================

migrate: ## Apply all pending Alembic migrations
	$(BACKEND) alembic upgrade head
	@echo "✅ Migrations applied"

migrate-create: ## Create a new Alembic migration (usage: make migrate-create MSG="add users table")
	$(BACKEND) alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Downgrade one migration
	$(BACKEND) alembic downgrade -1

migrate-history: ## Show migration history
	$(BACKEND) alembic history --verbose

db-reset: ## Drop and recreate database (DANGER: destroys all data)
	@echo "⚠️  WARNING: This will destroy all data. Press Ctrl+C to cancel."
	@sleep 3
	$(BACKEND) alembic downgrade base
	$(BACKEND) alembic upgrade head
	@echo "✅ Database reset complete"

db-shell: ## Open a PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U testpilot -d testpilot

# ==============================================================================
# Testing
# ==============================================================================

test: ## Run all backend tests
	$(POETRY) pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(POETRY) pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: backend/htmlcov/index.html"

test-unit: ## Run only unit tests
	$(POETRY) pytest tests/ -v -m unit --tb=short

test-integration: ## Run only integration tests
	$(POETRY) pytest tests/ -v -m integration --tb=short

# ==============================================================================
# Code Quality
# ==============================================================================

lint: ## Run ruff linter
	$(POETRY) ruff check app/ tests/

lint-fix: ## Run ruff linter with auto-fix
	$(POETRY) ruff check app/ tests/ --fix

format: ## Format code with black
	$(POETRY) black app/ tests/

format-check: ## Check formatting without changing files
	$(POETRY) black app/ tests/ --check

typecheck: ## Run mypy type checker
	$(POETRY) mypy app/ --ignore-missing-imports

check: lint typecheck format-check ## Run all quality checks

# ==============================================================================
# Utilities
# ==============================================================================

shell: ## Open a shell in the backend container
	$(DOCKER_COMPOSE) exec backend bash

redis-cli: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli -a $$REDIS_PASSWORD

qdrant-ui: ## Open Qdrant dashboard in browser
	@echo "🔍 Qdrant UI: http://localhost:6333/dashboard"
	@start http://localhost:6333/dashboard 2>/dev/null || open http://localhost:6333/dashboard

flower: ## Open Celery Flower in browser
	@start http://localhost:5555 2>/dev/null || open http://localhost:5555

# ==============================================================================
# TestPilot-specific
# ==============================================================================

index-repo: ## Index a repository (usage: make index-repo REPO_URL=https://github.com/owner/repo)
	@curl -X POST http://localhost:8000/api/v1/repositories/index \
		-H "Content-Type: application/json" \
		-d '{"clone_url": "$(REPO_URL)"}'

# ==============================================================================
# Cleanup
# ==============================================================================

clean: ## Remove Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete

clean-volumes: ## Remove all Docker volumes (DANGER: destroys all data)
	@echo "⚠️  WARNING: This will destroy all data. Press Ctrl+C to cancel."
	@sleep 3
	$(DOCKER_COMPOSE) down -v
	@echo "✅ Volumes removed"
