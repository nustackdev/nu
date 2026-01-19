"""Complex number type for Shape system.

Complex numbers for working with Python's built-in complex type.

This module provides Shape-compatible `ComplexType`, `ComplexRef`, and `ComplexSlot`.

Example:
    from everybase.type import ComplexSlot

    class Signal(Shape):
        amplitude = ComplexSlot()
        phase = ComplexSlot()

    # Operations
    Signal.amplitude.set(complex(3, 4))
    Signal.amplitude.get().real()
    Signal.amplitude.get().imag()
"""

from __future__ import annotations

from .args import ComplexArg
from .ref import ComplexRef
from .slot import ComplexSlot
from .type import ComplexType


__all__ = [
    "ComplexType",
    "ComplexRef",
    "ComplexArg",
    "ComplexSlot",
]
