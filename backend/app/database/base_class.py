"""
TestPilot AI — SQLAlchemy Declarative Base Class.

This module ONLY defines the Base class. Models import from here.
The actual all-models registration is in database/base.py for Alembic discovery.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class.

    All ORM models should inherit from this class. Provides a shared
    metadata registry for use with Alembic migrations.
    """

    pass
