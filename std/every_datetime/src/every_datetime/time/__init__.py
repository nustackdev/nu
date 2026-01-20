"""Time type for Shape system.

Provides TimeType, TimeRef, and TimeSlot for working with
Python time objects.

Example:
    from everybase.type import TimeSlot

    class Schedule(Shape):
        start_time = TimeSlot()
        end_time = TimeSlot()

    # Operations
    Schedule.start_time.set(time(9, 0))
    Schedule.start_time.get().hour()
"""

from __future__ import annotations

from .args import TimeArg
from .ref import TimeRef
from .slot import TimeSlot
from .type import TimeType


__all__ = [
    "TimeType",
    "TimeRef",
    "TimeSlot",
    "TimeArg",
]
