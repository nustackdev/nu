"""Timezone type for Shape system.

Provides TimezoneType, TimezoneRef, and TimezoneSlot for working with
Python timezone objects.

Example:
    from everybase.type import TimezoneSlot

    class Event(Shape):
        tz = TimezoneSlot()

    # Operations
    Event.tz.set(timezone.utc)
    Event.tz.get().tzname(None)
"""

from __future__ import annotations

from .args import TimezoneArg
from .ref import TimezoneRef
from .slot import TimezoneSlot
from .type import TimezoneType


__all__ = [
    "TimezoneType",
    "TimezoneRef",
    "TimezoneArg",
    "TimezoneSlot",
]
