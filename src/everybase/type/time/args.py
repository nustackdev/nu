"""Time args."""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "TimeArg",
]

type TimeArg = Arg[time]
