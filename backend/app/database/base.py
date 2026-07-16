"""
TestPilot AI — SQLAlchemy Base Registry for Alembic.

Imports Base from base_class and all models so Alembic can discover
them during autogenerate. Models import Base from base_class, NOT here,
to avoid circular imports.
"""

from app.database.base_class import Base  # noqa: F401 — re-export for Alembic env.py

# Import all models here so Alembic can discover them for migration generation.
# All models import Base from app.database.base_class to avoid circular imports.
from app.models.user import User  # noqa: E402, F401
from app.models.repository import Repository  # noqa: E402, F401
from app.models.pull_request import PullRequest  # noqa: E402, F401
from app.models.commit import Commit  # noqa: E402, F401
from app.models.repository_file import RepositoryFile  # noqa: E402, F401
from app.models.dependency_graph import DependencyEdge  # noqa: E402, F401
from app.models.generated_test import GeneratedTest  # noqa: E402, F401
from app.models.test_run import TestRun  # noqa: E402, F401
from app.models.test_result import TestResult  # noqa: E402, F401
from app.models.review_comment import ReviewComment  # noqa: E402, F401
from app.models.ai_log import AILog  # noqa: E402, F401
from app.models.agent_run import AgentRun  # noqa: E402, F401
from app.models.bug_history import BugHistory  # noqa: E402, F401
