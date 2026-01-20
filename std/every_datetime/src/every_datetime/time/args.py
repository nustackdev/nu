"""Time args."""

from __future__ import annotations

from datetime import time

from every._abc import Arg


__all__ = [
    "TimeArg",
]

type TimeArg = Arg[time]
