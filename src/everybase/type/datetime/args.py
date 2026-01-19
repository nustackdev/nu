"""Datetime args."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from everybase.type.timezone.args import TimezoneArg
from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "DatetimeArg",
    "TimezoneArg",
]

type DatetimeArg = Arg[datetime]
