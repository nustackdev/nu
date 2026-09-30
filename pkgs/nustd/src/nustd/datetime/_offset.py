"""A fixed UTC offset spelled as text reads back as the timezone it spells.

Both fabrics store a ``datetime.timezone`` as ``str(timezone)`` (``"UTC"`` or
``"UTC+05:30"``); this is the one parser that lifts that text back.
"""

from __future__ import annotations

from datetime import timedelta, timezone


__all__ = ["UTC", "parse_timezone"]


UTC = timezone.utc


def parse_timezone(raw: str) -> timezone:
    """Parse ``str(timezone)`` output (``"UTC"`` or ``"UTC+05:30"``)."""
    s = raw[3:] if raw.startswith("UTC") else raw
    if not s:
        return UTC
    sign = 1 if s[0] == "+" else -1
    parts = s[1:].split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))
