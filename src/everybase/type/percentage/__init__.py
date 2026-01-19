"""Percentage type for Shape system.

Percentages stored as float (0.0 to 100.0+).
Use BasisPoint for more precise rate representations.

This module provides both a native Python `Percentage` class and
Shape-compatible `PercentageType`, `PercentageRef`, and `PercentageSlot`.

Example:
    from everybase.type import PercentageSlot

    class Progress(Shape):
        completion = PercentageSlot()

    Progress.completion.set(Percentage(75.5))
    Progress.completion.to_dec()   # 0.755
    Progress.completion.apply(200) # 151.0
"""

from __future__ import annotations

from .args import PercentageArg
from .cls import Percentage
from .ref import PercentageRef
from .slot import PercentageSlot
from .type import PercentageType


__all__ = [
    "Percentage",
    "PercentageType",
    "PercentageRef",
    "PercentageSlot",
    "PercentageArg",
]
