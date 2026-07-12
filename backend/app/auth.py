from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import MAGIC_LINK_TTL_MINUTES, SESSION_TTL_DAYS
from app.email import EmailSender
from app.orm import AuthSession, MagicLink, User
from app.time import utcnow


class AuthError(Exception):
    """Raised when a login link or session is missing, expired, or reused."""


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    # Login and session tokens are full-entropy random values, so a plain
    # SHA-256 (no per-value salt) is sufficient and lets us look them up by
    # hash. Raw tokens are never stored.
    return hashlib.sha256(token.encode()).hexdigest()


def _normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise AuthError("a valid email address is required")
    return email


def _strip_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AuthError("authentication required")
    scheme, _, token = authorization.partition(" ")
    token = token.strip() if token else scheme.strip()
    if not token:
        raise AuthError("authentication required")
    return token


def request_magic_link(session: Session, email: str, sender: EmailSender) -> str:
    """Create a single-use login token for the email and send it. The user is
    created on first sight. Returns the raw token for the caller to decide
    whether to expose it (dev only)."""
    address = _normalize_email(email)

    user = session.scalar(select(User).where(User.email == address))
    if user is None:
        user = User(email=address)
        session.add(user)
        session.flush()

    raw_token = _generate_token()
    session.add(
        MagicLink(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=MAGIC_LINK_TTL_MINUTES),
        )
    )
    session.commit()

    sender.send_magic_link(address, raw_token)
    return raw_token


def verify_magic_link(session: Session, raw_token: str) -> str:
    """Consume a login token and return a new session bearer token."""
    link = session.scalar(
        select(MagicLink).where(MagicLink.token_hash == _hash_token(raw_token))
    )
    if link is None or link.used_at is not None or link.expires_at < utcnow():
        raise AuthError("login link is invalid or expired")

    link.used_at = utcnow()

    raw_session = _generate_token()
    session.add(
        AuthSession(
            user_id=link.user_id,
            token_hash=_hash_token(raw_session),
            expires_at=utcnow() + timedelta(days=SESSION_TTL_DAYS),
        )
    )
    session.commit()
    return raw_session


def resolve_user(session: Session, authorization: str | None) -> User:
    """Return the user for a bearer session token, or raise AuthError."""
    token = _strip_bearer(authorization)
    auth_session = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _hash_token(token))
    )
    if auth_session is None or auth_session.expires_at < utcnow():
        raise AuthError("session is invalid or expired")

    user = session.get(User, auth_session.user_id)
    if user is None:
        raise AuthError("session is invalid or expired")
    return user


def logout(session: Session, authorization: str | None) -> None:
    """Revoke the session behind a bearer token. No-op if it is already gone."""
    try:
        token = _strip_bearer(authorization)
    except AuthError:
        return
    auth_session = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _hash_token(token))
    )
    if auth_session is not None:
        session.delete(auth_session)
        session.commit()
