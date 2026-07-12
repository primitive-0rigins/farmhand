from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_database_url


class Base(DeclarativeBase):
    pass


# create_engine does not open a connection until first use, so importing this
# module never touches the database. Tables are created by init_db() at app
# startup; tests build their own in-memory engine instead.
engine = create_engine(get_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create tables for a brand-new schema.

    This bootstraps the schema directly from the models. Production schema
    evolution should move to Alembic; that is deferred here because a real
    Postgres migration cannot be validated in this environment.
    """
    import app.orm  # noqa: F401  -- register mapped models on Base.metadata

    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
