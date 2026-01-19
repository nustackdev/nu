"""Percentage args."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    from .cls import Percentage


__all__ = [
    "PercentageArg",
]

type PercentageArg = Arg[Percentage]
