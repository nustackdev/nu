"""Date args."""

from __future__ import annotations

from datetime import date

from every._abc import Arg


__all__ = [
    "DateArg",
]

type DateArg = Arg[date]
