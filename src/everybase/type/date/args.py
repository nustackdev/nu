"""Date args."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "DateArg",
]

type DateArg = Arg[date]
