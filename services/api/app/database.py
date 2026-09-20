"""
NEXUS Database Engine and Session Factory.
Provides managed SQLAlchemy engines, sessions, and lifecycles.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from services.api.app.config import get_settings

Base = declarative_base()

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """Get or initialize the SQLAlchemy database engine."""
    global _engine, _session_factory
    url = database_url or get_settings().DATABASE_URL

    if _engine is None or str(_engine.url) != url:
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
    return _engine


def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Get the SQLAlchemy session factory."""
    get_engine(database_url)
    assert _session_factory is not None
    return _session_factory


def get_db(database_url: str | None = None) -> Generator[Session, None, None]:
    """Yield a database session for request lifecycle / dependency injection."""
    factory = get_session_factory(database_url)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def close_engine() -> None:
    """Dispose of the database connection pool."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
