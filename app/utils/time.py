from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")
