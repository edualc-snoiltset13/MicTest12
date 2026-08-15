"""SQLAlchemy engine/session wiring.

The framework must run identically on SQLite (developer laptops, CI, the
Cypress fixture server) and PostgreSQL (staging/production), so all engine
tuning that differs between the two lives here and nowhere else.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import Settings, get_settings


class Base(DeclarativeBase):
    """Declarative base for every ORM model in the service."""


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine(settings: Settings) -> Engine:
    if settings.is_sqlite:
        connect_args = {"check_same_thread": False}
        kwargs: dict[str, object] = {"connect_args": connect_args}
        # ``:memory:`` databases must share a single connection or each session
        # would see an empty schema.
        if ":memory:" in settings.database_url:
            kwargs["poolclass"] = StaticPool
        engine = create_engine(settings.database_url, echo=settings.sql_echo, future=True, **kwargs)

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            # Referential integrity is off by default in SQLite; the cascade
            # deletes on lab panels/results depend on it.
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        return engine

    return create_engine(
        settings.database_url,
        echo=settings.sql_echo,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings())
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _SessionLocal


def dispose_engine() -> None:
    """Tear down engine + session factory (used between test modules)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for scripts/seeders that live outside the request cycle."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all() -> None:
    """Create the schema. Alembic owns migrations in production; this is for
    local dev, CI and the ephemeral QA fixture database."""
    from . import models  # noqa: F401  (import registers the mappers)

    Base.metadata.create_all(bind=get_engine())


def drop_all() -> None:
    from . import models  # noqa: F401

    Base.metadata.drop_all(bind=get_engine())
