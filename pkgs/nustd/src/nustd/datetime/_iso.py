"""ISO parsing that reads a trailing ``Z`` as UTC on every supported Python.

3.11 widened ``fromisoformat`` to accept ``Z``; 3.10 rejects it. A value
written as ``"...Z"`` would store fine and fail on read, so both fabrics and
the ``FromIso`` atoms parse through here.
"""

from __future__ import annotations

import sys
from datetime import datetime, time


__all__ = ["datetime_from_iso", "time_from_iso"]


def _utc_z(s: str) -> str:
    return s[:-1] + "+00:00" if s.endswith(("Z", "z")) else s


if sys.version_info >= (3, 11):
    datetime_from_iso = datetime.fromisoformat
    time_from_iso = time.fromisoformat
else:

    def datetime_from_iso(s: str) -> datetime:
        """``datetime.fromisoformat`` that also reads a trailing ``Z`` as UTC."""
        return datetime.fromisoformat(_utc_z(s))

    def time_from_iso(s: str) -> time:
        """``time.fromisoformat`` that also reads a trailing ``Z`` as UTC."""
        return time.fromisoformat(_utc_z(s))
