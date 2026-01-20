"""Datetime type for Shape system.

Provides DatetimeType, DatetimeRef, and DatetimeSlot for working with
Python datetime objects.

Example:
    from everybase.type import DatetimeSlot

    class Event(Shape):
        created_at = DatetimeSlot()
        updated_at = DatetimeSlot()

    # Operations
    Event.created_at.set(datetime.now())
    Event.created_at.get()
    Event.created_at.get().timestamp()
"""

from __future__ import annotations

from .args import DatetimeArg
from .ref import DatetimeRef
from .slot import DatetimeSlot
from .type import DatetimeType


__all__ = [
    "DatetimeType",
    "DatetimeRef",
    "DatetimeSlot",
    "DatetimeArg",
]
