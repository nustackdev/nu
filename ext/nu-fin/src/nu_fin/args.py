"""Type argument aliases for financial types."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Arg


if TYPE_CHECKING:
    from .basis_point_cls import BasisPoint
    from .percentage_cls import Percentage


__all__ = [
    "BasisPointArg",
    "PercentageArg",
]

type BasisPointArg = Arg["BasisPoint | int"]
type PercentageArg = Arg["Percentage | float"]
