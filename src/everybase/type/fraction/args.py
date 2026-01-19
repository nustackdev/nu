"""Fraction args."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "FractionArg",
]

type FractionArg = Arg[Fraction]
