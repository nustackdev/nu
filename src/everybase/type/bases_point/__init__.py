"""Basis Point.

Basis points (bps) are 1/100th of a percent:
- 1 bp = 0.01%
- 100 bps = 1%
- 10000 bps = 100%

This module provides both a native Python `BasisPoint` class and
Shape-compatible `BasisPointType`, `BasisPointRef`, and `BasisPointSlot`.

Example:
    from everybase.type import BasisPointSlot

    class TradeConfig(Shape):
        slippage = BasisPointSlot()  # 500 = 5%

    TradeConfig.slippage.set(BasisPoint(500))
    TradeConfig.slippage.to_pct()    # 5.0
    TradeConfig.slippage.to_dec()    # 0.05
"""

from __future__ import annotations

from .cls import BasisPoint
from .ref import BasisPointRef
from .slot import BasisPointSlot
from .type import BasisPointType


__all__ = [
    "BasisPoint",
    "BasisPointType",
    "BasisPointRef",
    "BasisPointSlot",
]
