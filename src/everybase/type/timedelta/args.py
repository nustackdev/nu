"""Timedelta args."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    from .type import TimedeltaType


__all__ = [
    "TimedeltaArg",
]

type TimedeltaArg = Arg[timedelta | TimedeltaType]
