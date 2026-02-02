"""Type argument aliases for math types."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from everyabc import Arg


__all__ = [
    "ComplexArg",
    "DecimalArg",
    "FractionArg",
]

type DecimalArg = Arg[Decimal | int | float | str]
type FractionArg = Arg[Fraction | int | float | str]
type ComplexArg = Arg[complex | int | float]
