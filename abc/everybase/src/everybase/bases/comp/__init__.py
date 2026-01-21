"""Bases for computations.

TODO: atm for ops only, generalize for Computation class.
"""

from __future__ import annotations

from .binary import BinaryOp
from .nary import NAryOp
from .ternary import TernaryOp
from .unary import UnaryOp


__all__ = [
    "BinaryOp",
    "NAryOp",
    "TernaryOp",
    "UnaryOp",
]
