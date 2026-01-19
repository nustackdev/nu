"""Decimal args."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "DecimalArg",
]

type DecimalArg = Arg[Decimal]
