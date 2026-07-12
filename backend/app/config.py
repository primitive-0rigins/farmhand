from __future__ import annotations

import os

DEFAULT_ALLOWED_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


def get_allowed_origins() -> list[str]:
    configured = os.getenv("FARMHAND_ALLOWED_ORIGINS")
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)

    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return origins or list(DEFAULT_ALLOWED_ORIGINS)


DEFAULT_DATABASE_URL = "sqlite:///./farmhand.db"

# Passwordless login lifetimes.
MAGIC_LINK_TTL_MINUTES = 15
SESSION_TTL_DAYS = 30


def get_database_url() -> str:
    return os.getenv("FARMHAND_DATABASE_URL", DEFAULT_DATABASE_URL)


def dev_auth_enabled() -> bool:
    """When true, /auth/request also returns the magic-link token in its
    response so the flow can be exercised without email. This is a development
    convenience and MUST stay off in production; the token otherwise goes only
    to the email sender (the console in dev)."""
    return os.getenv("FARMHAND_DEV_AUTH", "0") == "1"
