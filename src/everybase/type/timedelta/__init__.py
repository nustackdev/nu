"""Timedelta type for Shape system.

Provides TimedeltaType, TimedeltaRef, and TimedeltaSlot for working with
Python timedelta objects.

Example:
    from everybase.type import TimedeltaSlot

    class Task(Shape):
        duration = TimedeltaSlot()
        timeout = TimedeltaSlot()

    # Operations
    Task.duration.set(timedelta(hours=2))
    Task.duration.get().total_seconds()
"""

from __future__ import annotations

from .args import TimedeltaArg
from .ref import TimedeltaRef
from .slot import TimedeltaSlot
from .type import TimedeltaType


__all__ = [
    "TimedeltaType",
    "TimedeltaRef",
    "TimedeltaSlot",
    "TimedeltaArg",
]
