from datetime import timedelta

import pytest
from sqlalchemy import select

from app.auth import (
    AuthError,
    logout,
    request_magic_link,
    resolve_user,
    verify_magic_link,
)
from app.orm import AuthSession, MagicLink, User
from app.time import utcnow
from tests.conftest import RecordingEmailSender


def _login(db) -> str:
    sender = RecordingEmailSender()
    request_magic_link(db, "Farmer@Example.com", sender)
    assert sender.last_token is not None
    return verify_magic_link(db, sender.last_token)


def test_request_creates_user_once_and_sends_token(db) -> None:
    sender = RecordingEmailSender()

    request_magic_link(db, "farmer@example.com", sender)
    request_magic_link(db, "FARMER@example.com", sender)  # same user, normalized

    users = db.scalars(select(User)).all()
    assert len(users) == 1
    assert users[0].email == "farmer@example.com"
    assert sender.last_token is not None


def test_verify_issues_a_working_session(db) -> None:
    token = _login(db)
    user = resolve_user(db, f"Bearer {token}")
    assert user.email == "farmer@example.com"


def test_bad_email_is_rejected(db) -> None:
    with pytest.raises(AuthError):
        request_magic_link(db, "not-an-email", RecordingEmailSender())


def test_missing_or_garbage_bearer_is_rejected(db) -> None:
    with pytest.raises(AuthError):
        resolve_user(db, None)
    with pytest.raises(AuthError):
        resolve_user(db, "Bearer not-a-real-token")


def test_expired_magic_link_is_rejected(db) -> None:
    sender = RecordingEmailSender()
    request_magic_link(db, "farmer@example.com", sender)
    link = db.scalar(select(MagicLink))
    link.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()

    with pytest.raises(AuthError):
        verify_magic_link(db, sender.last_token)


def test_magic_link_is_single_use(db) -> None:
    sender = RecordingEmailSender()
    request_magic_link(db, "farmer@example.com", sender)

    verify_magic_link(db, sender.last_token)
    with pytest.raises(AuthError):
        verify_magic_link(db, sender.last_token)


def test_expired_session_is_rejected(db) -> None:
    token = _login(db)
    session_row = db.scalar(select(AuthSession))
    session_row.expires_at = utcnow() - timedelta(days=1)
    db.commit()

    with pytest.raises(AuthError):
        resolve_user(db, f"Bearer {token}")


def test_logout_revokes_the_session(db) -> None:
    token = _login(db)
    logout(db, f"Bearer {token}")

    assert db.scalar(select(AuthSession)) is None
    with pytest.raises(AuthError):
        resolve_user(db, f"Bearer {token}")


def test_stored_tokens_are_hashed_not_raw(db) -> None:
    sender = RecordingEmailSender()
    request_magic_link(db, "farmer@example.com", sender)

    link = db.scalar(select(MagicLink))
    assert link.token_hash != sender.last_token
    assert len(link.token_hash) == 64  # sha256 hex
