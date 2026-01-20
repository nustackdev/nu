"""Complex Ref."""

from __future__ import annotations

from term.ops import FuncCallOp

from every._abc import RValue
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .type import ComplexType


__all__ = [
    "ComplexRef",
]


def _parse_complex_str(s: str) -> complex:
    """Parse complex number from 'real,imag' format."""
    parts = s.split(",")
    return complex(float(parts[0]), float(parts[1]))


def _format_complex(c: complex) -> str:
    """Format complex number to 'real,imag' format."""
    return f"{c.real},{c.imag}"


class ComplexRef(CollectionItemRefBase[complex, ComplexType], PrimitiveRef):
    """Reference to a complex value in storage.

    Complex values are stored as "real,imag" strings.

    Example:
        class Signal(Shape):
            amplitude = ComplexSlot()

        Signal.amplitude.set(complex(3, 4))
        Signal.amplitude.get()  # Returns ComplexType
    """

    def set(self, value: complex | str | RValue) -> ComplexType:
        """Set the complex value.

        Args:
            value: Complex number or string to store.

        Returns:
            ComplexType representing the set operation result.
        """
        if isinstance(value, complex):
            val = _format_complex(value)
        elif isinstance(value, str):
            val = value
        else:
            # Create a formatted string from the RValue
            val = FuncCallOp(_format_complex, value)
        return ComplexType(TypedSetCmd(self, val))

    def get(self) -> ComplexType:
        """Get the complex value.

        Returns:
            ComplexType from storage.
        """
        return ComplexType(FuncCallOp(_parse_complex_str, GetOp(self)))
