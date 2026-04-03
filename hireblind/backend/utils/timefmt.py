"""Consistent UTC ISO strings for API responses (SQLite often returns naive datetimes)."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()
