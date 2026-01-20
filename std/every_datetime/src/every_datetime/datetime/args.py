"""Datetime args."""

from __future__ import annotations

from datetime import datetime

from every._abc import Arg
from everybase.type.timezone.args import TimezoneArg


__all__ = [
    "DatetimeArg",
    "TimezoneArg",
]

type DatetimeArg = Arg[datetime]
