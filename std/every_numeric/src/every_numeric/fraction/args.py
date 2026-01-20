"""Fraction args."""

from __future__ import annotations

from fractions import Fraction

from every._abc import Arg


__all__ = [
    "FractionArg",
]

type FractionArg = Arg[Fraction]
