"""
Integration tests for database connectivity and SQLAlchemy engine lifecycle.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from services.api.app.config import get_settings
from services.api.app.database import close_engine, get_engine


def test_database_connection():
    """Verify application can establish a live connection to PostgreSQL."""
    settings = get_settings()
    engine = get_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            val = result.scalar()
            assert val == 1, "Expected SELECT 1 to return 1"
    except OperationalError as exc:
        pytest.skip(
            f"PostgreSQL service is not running or unreachable at {settings.DATABASE_URL}: {exc}"
        )
    finally:
        close_engine()
