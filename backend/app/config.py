from __future__ import annotations

import os

DEFAULT_ALLOWED_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


def get_allowed_origins() -> list[str]:
    configured = os.getenv("FARMHAND_ALLOWED_ORIGINS")
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)

    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return origins or list(DEFAULT_ALLOWED_ORIGINS)
