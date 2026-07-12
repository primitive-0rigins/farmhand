from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.orm  # noqa: F401  -- register mapped models on Base.metadata
from app.db import Base


@pytest.fixture
def db() -> Iterator[Session]:
    # StaticPool keeps a single connection so an in-memory SQLite database
    # persists for the whole test instead of vanishing per connection.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False, future=True)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class RecordingEmailSender:
    """Captures the last magic-link token instead of sending an email."""

    def __init__(self) -> None:
        self.last_token: str | None = None

    def send_magic_link(self, email: str, token: str) -> None:
        self.last_token = token
