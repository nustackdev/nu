"""Date type for Shape system.

Provides DateType, DateRef, and DateSlot for working with
Python date objects.

Example:
    from everybase.type import DateSlot

    class Person(Shape):
        birth_date = DateSlot()
        hire_date = DateSlot()

    # Operations
    Person.birth_date.set(date.today())
    Person.birth_date.get().year()
"""

from __future__ import annotations

from .args import DateArg
from .ref import DateRef
from .slot import DateSlot
from .type import DateType


__all__ = [
    "DateType",
    "DateRef",
    "DateSlot",
    "DateArg",
]
