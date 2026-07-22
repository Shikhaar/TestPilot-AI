"""
TestPilot AI Backend — Core Configuration.

Uses Pydantic Settings for type-safe, environment-variable-driven configuration.
All settings are loaded from the environment / .env file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All values can be overridden via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # --------------------------------------------------------------------------
    # Application
    # --------------------------------------------------------------------------
    app_name: str = Field(default="TestPilot AI", description="Application name")
    app_env: str = Field(
        default="development", description="Environment: development|staging|production"
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    secret_key: str = Field(
        default="change-me-to-a-long-random-string", description="Secret key for signing tokens"
    )
    allowed_origins_str: str = Field(
        default="http://localhost:3000",
        alias="ALLOWED_ORIGINS",
        description="CORS allowed origins (comma-separated or JSON array)",
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list at access time."""
        v = self.allowed_origins_str.strip()
        if v.startswith("["):
            try:
                res = json.loads(v)
                if isinstance(res, list):
                    return [str(item) for item in res]
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    # --------------------------------------------------------------------------
    # Database
    # --------------------------------------------------------------------------
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="testpilot")
    postgres_password: str = Field(default="testpilot_secret")
    postgres_db: str = Field(default="testpilot")
    database_url: str = Field(
        default="postgresql+asyncpg://testpilot:testpilot_secret@localhost:5432/testpilot"
    )

    # SQLAlchemy pool settings
    db_pool_size: int = Field(default=20)
    db_max_overflow: int = Field(default=40)
    db_pool_timeout: int = Field(default=30)
    db_pool_recycle: int = Field(default=3600)
    db_echo: bool = Field(default=False)

    # --------------------------------------------------------------------------
    # Redis
    # --------------------------------------------------------------------------
    redis_url: str = Field(default="redis://:redis_secret@localhost:6379/0")
    celery_broker_url: str = Field(default="redis://:redis_secret@localhost:6379/0")
    celery_result_backend: str = Field(default="redis://:redis_secret@localhost:6379/1")

    # --------------------------------------------------------------------------
    # Qdrant
    # --------------------------------------------------------------------------
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_api_key: str = Field(default="qdrant_secret")
    qdrant_url: str = Field(default="http://localhost:6333")

    # Qdrant collection names
    qdrant_collection_repository_chunks: str = Field(default="repository_chunks")
    qdrant_collection_functions: str = Field(default="functions")
    qdrant_collection_classes: str = Field(default="classes")
    qdrant_collection_tests: str = Field(default="tests")
    qdrant_collection_bug_history: str = Field(default="bug_history")
    qdrant_collection_pr_reviews: str = Field(default="pr_reviews")

    # Embedding dimensions
    embedding_dimensions: int = Field(default=1536, description="Dimension of embedding vectors")

    # --------------------------------------------------------------------------
    # GitHub App
    # --------------------------------------------------------------------------
    github_app_id: str = Field(default="")
    github_app_private_key_path: Path = Field(default=Path("/secrets/github-private-key.pem"))
    github_webhook_secret: str = Field(default="your-webhook-secret")
    github_client_id: str = Field(default="")
    github_client_secret: str = Field(default="")
    github_app_name: str = Field(default="testpilot-ai-app")

    @property
    def github_private_key(self) -> str | None:
        """Load GitHub App private key from file."""
        path = self.github_app_private_key_path
        if path.exists():
            return path.read_text()
        return None

    # --------------------------------------------------------------------------
    # JWT
    # --------------------------------------------------------------------------
    jwt_secret_key: str = Field(default="change-me-to-another-long-random-key")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)
    jwt_refresh_token_expire_days: int = Field(default=30)

    # --------------------------------------------------------------------------
    # LiteLLM / AI
    # --------------------------------------------------------------------------
    openai_api_key: str = Field(default="sk-placeholder")
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    litellm_default_model: str = Field(default="gemini/gemini-2.0-flash")
    litellm_fallback_model: str = Field(default="gemini/gemini-1.5-flash")
    litellm_embedding_model: str = Field(default="text-embedding-3-small")
    ollama_host: str = Field(default="http://localhost:11434")
    anthropic_api_key: str = Field(default="")

    # Sentence Transformers (local embeddings)
    sentence_transformer_model: str = Field(default="all-MiniLM-L6-v2")
    use_local_embeddings: bool = Field(default=True)

    # LLM settings
    llm_temperature: float = Field(default=0.0)
    llm_max_tokens: int = Field(default=4096)
    llm_timeout: int = Field(default=120)
    llm_max_retries: int = Field(default=3)

    # --------------------------------------------------------------------------
    # Repository Storage
    # --------------------------------------------------------------------------
    repo_storage_path: Path = Field(default=Path("/tmp/repos"))
    max_repo_size_mb: int = Field(default=500)

    # Files/directories to ignore during indexing
    ignored_directories: list[str] = Field(
        default=[
            "node_modules",
            "dist",
            "build",
            ".venv",
            "venv",
            ".git",
            "target",
            "vendor",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "coverage",
            "htmlcov",
            ".next",
            "out",
        ]
    )
    ignored_extensions: list[str] = Field(
        default=[".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe", ".bin"]
    )

    # --------------------------------------------------------------------------
    # Test Execution
    # --------------------------------------------------------------------------
    test_execution_timeout_seconds: int = Field(default=300)
    test_execution_max_parallel: int = Field(default=4)
    coverage_threshold: float = Field(default=80.0)

    # --------------------------------------------------------------------------
    # Observability
    # --------------------------------------------------------------------------
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")
    otel_service_name: str = Field(default="testpilot-ai")
    otel_environment: str = Field(default="development")
    prometheus_enabled: bool = Field(default=True)

    # --------------------------------------------------------------------------
    # Rate Limiting
    # --------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=100)

    # --------------------------------------------------------------------------
    # Derived Properties
    # --------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()


# Convenience alias for dependency injection
settings = get_settings()
