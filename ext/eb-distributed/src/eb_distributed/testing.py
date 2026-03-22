"""Test utilities for eb-distributed.

Shapes and helpers used in tests. Defined here (importable module)
so they survive pickling across Ray actor processes.
"""

from __future__ import annotations

import eb_virtuals as ebv
from everybase.shape import Shape


__all__ = [
    "TestShape",
]


class TestShape(Shape):
    """Test shape with price and quantity fields."""

    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()
