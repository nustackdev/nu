"""Complex type for complex number arithmetic.

Pattern:
    ComplexType = Object[complex] + EqualableBase + arithmetic operations
    ComplexValue = ValueBase + ComplexType (computed results)

Note: Complex numbers are not orderable (no <, >, <=, >=).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Sentinel
from everybase.abc import (
    EqualableBase,
    FloatValue,
    Object,
    TupleValue,
    ValueBase,
)


if TYPE_CHECKING:
    from everybase import Term

    from .args import ComplexArg


__all__ = [
    "ComplexType",
    "ComplexValue",
]


class ComplexType(
    EqualableBase["complex | ComplexType"],
    Object[complex | Sentinel],
):
    """Abstract type for complex number operations.

    Supports complex arithmetic and component access.
    Uses *Type in arguments (loose variance), returns *Value (specific).

    Note: Complex numbers are not orderable (no <, >, <=, >=).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        real: float | Term[float] = 0,
        imag: float | Term[float] = 0,
    ) -> ComplexValue:
        """Create a ComplexValue from real and imaginary parts."""
        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(complex, real, imag))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> ComplexValue:
        """Create a ComplexValue from a string."""
        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(complex, value))

    @classmethod
    def from_polar(cls, r: float | Term[float], phi: float | Term[float]) -> ComplexValue:
        """Create a ComplexValue from polar coordinates."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.rect, r, phi))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def real(self) -> FloatValue:
        """Get the real part."""
        from everybase.abc import FuncCallOp

        return FloatValue(FuncCallOp(getattr, self, "real"))

    def imag(self) -> FloatValue:
        """Get the imaginary part."""
        from everybase.abc import FuncCallOp

        return FloatValue(FuncCallOp(getattr, self, "imag"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: ComplexArg) -> ComplexValue:
        """Add complex numbers."""
        from everybase.abc import AddOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(AddOp(self, other))

    def __radd__(self, other: complex | int | float) -> ComplexValue:
        """Right add."""
        from everybase.abc import AddOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(AddOp(other, self))

    def __sub__(self, other: ComplexArg) -> ComplexValue:
        """Subtract complex numbers."""
        from everybase.abc import SubOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(SubOp(self, other))

    def __rsub__(self, other: complex | int | float) -> ComplexValue:
        """Right subtract."""
        from everybase.abc import SubOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(SubOp(other, self))

    def __mul__(self, other: ComplexArg) -> ComplexValue:
        """Multiply complex numbers."""
        from everybase.abc import MulOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(MulOp(self, other))

    def __rmul__(self, other: complex | int | float) -> ComplexValue:
        """Right multiply."""
        from everybase.abc import MulOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(MulOp(other, self))

    def __truediv__(self, other: ComplexArg) -> ComplexValue:
        """Divide complex numbers."""
        from everybase.abc import DivOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(DivOp(self, other))

    def __rtruediv__(self, other: complex | int | float) -> ComplexValue:
        """Right divide."""
        from everybase.abc import DivOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(DivOp(other, self))

    def __pow__(self, other: ComplexArg) -> ComplexValue:
        """Raise to power."""
        from everybase.abc import PowOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(PowOp(self, other))

    def __rpow__(self, other: complex | int | float) -> ComplexValue:
        """Right power."""
        from everybase.abc import PowOp

        if isinstance(other, complex):
            other = ComplexValue(other)
        return ComplexValue(PowOp(other, self))

    def __neg__(self) -> ComplexValue:
        """Negate."""
        from everybase.abc import NegOp

        return ComplexValue(NegOp(self))

    def __abs__(self) -> FloatValue:
        """Get magnitude (absolute value)."""
        from everybase.abc import FuncCallOp

        return FloatValue(FuncCallOp(abs, self))

    # =========================================================================
    # COMPLEX OPERATIONS
    # =========================================================================

    def conjugate(self) -> ComplexValue:
        """Get the complex conjugate."""
        from everybase.abc import MethodCallOp

        return ComplexValue(MethodCallOp(self, "conjugate"))

    def phase(self) -> FloatValue:
        """Get the phase angle in radians."""
        import cmath

        from everybase.abc import FuncCallOp

        return FloatValue(FuncCallOp(cmath.phase, self))

    def polar(self) -> TupleValue:
        """Get polar coordinates (r, phi)."""
        import cmath

        from everybase.abc import FuncCallOp

        return TupleValue(FuncCallOp(cmath.polar, self))

    # =========================================================================
    # MATHEMATICAL FUNCTIONS
    # =========================================================================

    def sqrt(self) -> ComplexValue:
        """Square root."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.sqrt, self))

    def exp(self) -> ComplexValue:
        """Exponential (e^self)."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.exp, self))

    def log(self, base: float | ComplexArg | None = None) -> ComplexValue:
        """Logarithm."""
        import cmath

        from everybase.abc import FuncCallOp

        if base is not None:
            return ComplexValue(FuncCallOp(cmath.log, self, base))
        return ComplexValue(FuncCallOp(cmath.log, self))

    def sin(self) -> ComplexValue:
        """Sine."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.sin, self))

    def cos(self) -> ComplexValue:
        """Cosine."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.cos, self))

    def tan(self) -> ComplexValue:
        """Tangent."""
        import cmath

        from everybase.abc import FuncCallOp

        return ComplexValue(FuncCallOp(cmath.tan, self))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class ComplexValue(ValueBase, ComplexType):
    """Computed complex value (Python memory substrate)."""

    pass
