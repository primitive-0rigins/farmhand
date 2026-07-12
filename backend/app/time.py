from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC 'now'.

    Stored timestamps stay naive so comparisons never mix aware and naive
    values -- SQLite drops timezone info on read, which would otherwise raise.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
