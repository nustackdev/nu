"""ComplexI - complex number interface.

ComplexI = TypedNu[complex] + arithmetic + equality + component access.
Complex numbers are not orderable (no <, >, <=, >=).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.collections import TupleI
    from nu.primitives import BoolI, FloatI

__all__ = [
    "ComplexArg",
    "ComplexI",
]

type ComplexArg = Arg[complex]


class _ComplexI(Interface):
    """Mixin for complex number operations.

    Supports complex arithmetic and component access.
    Complex numbers are not orderable (no <, >, <=, >=).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        real: float | Nu[float] = 0,
        imag: float | Nu[float] = 0,
    ) -> ComplexI:
        """Create a ComplexI from real and imaginary parts."""
        from nu import FuncCallOp

        return ComplexI(FuncCallOp(complex, real, imag))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> ComplexI:
        """Create a ComplexI from a string."""
        from nu import FuncCallOp

        return ComplexI(FuncCallOp(complex, value))

    @classmethod
    def from_polar(cls, r: float | Nu[float], phi: float | Nu[float]) -> ComplexI:
        """Create a ComplexI from polar coordinates."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.rect, r, phi))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def real(self) -> FloatI:
        """Get the real part."""
        from nu import FuncCallOp
        from nu.primitives import FloatI

        return FloatI(FuncCallOp(getattr, self, "real"))

    def imag(self) -> FloatI:
        """Get the imaginary part."""
        from nu import FuncCallOp
        from nu.primitives import FloatI

        return FloatI(FuncCallOp(getattr, self, "imag"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: ComplexArg) -> ComplexI:
        """Add complex numbers."""
        from nu import AddOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(AddOp(self, other))

    def __radd__(self, other: complex | int | float) -> ComplexI:
        """Right add."""
        from nu import AddOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(AddOp(other, self))

    def __sub__(self, other: ComplexArg) -> ComplexI:
        """Subtract complex numbers."""
        from nu import SubOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(SubOp(self, other))

    def __rsub__(self, other: complex | int | float) -> ComplexI:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(SubOp(other, self))

    def __mul__(self, other: ComplexArg) -> ComplexI:
        """Multiply complex numbers."""
        from nu import MulOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(MulOp(self, other))

    def __rmul__(self, other: complex | int | float) -> ComplexI:
        """Right multiply."""
        from nu import MulOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(MulOp(other, self))

    def __truediv__(self, other: ComplexArg) -> ComplexI:
        """Divide complex numbers."""
        from nu import DivOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(DivOp(self, other))

    def __rtruediv__(self, other: complex | int | float) -> ComplexI:
        """Right divide."""
        from nu import DivOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(DivOp(other, self))

    def __pow__(self, other: ComplexArg) -> ComplexI:
        """Raise to power."""
        from nu import PowOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(PowOp(self, other))

    def __rpow__(self, other: complex | int | float) -> ComplexI:
        """Right power."""
        from nu import PowOp

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(PowOp(other, self))

    def __neg__(self) -> ComplexI:
        """Negate."""
        from nu import NegOp

        return ComplexI(NegOp(self))

    def __abs__(self) -> FloatI:
        """Get magnitude (absolute value)."""
        from nu import FuncCallOp
        from nu.primitives import FloatI

        return FloatI(FuncCallOp(abs, self))

    # =========================================================================
    # COMPLEX OPERATIONS
    # =========================================================================

    def conjugate(self) -> ComplexI:
        """Get the complex conjugate."""
        from nu import MethodCallOp

        return ComplexI(MethodCallOp(self, "conjugate"))

    def phase(self) -> FloatI:
        """Get the phase angle in radians."""
        import cmath

        from nu import FuncCallOp
        from nu.primitives import FloatI

        return FloatI(FuncCallOp(cmath.phase, self))

    def polar(self) -> TupleI:
        """Get polar coordinates (r, phi)."""
        import cmath

        from nu import FuncCallOp
        from nu.collections import TupleI

        return TupleI(FuncCallOp(cmath.polar, self))

    # =========================================================================
    # MATHEMATICAL FUNCTIONS
    # =========================================================================

    def sqrt(self) -> ComplexI:
        """Square root."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.sqrt, self))

    def exp(self) -> ComplexI:
        """Exponential (e^self)."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.exp, self))

    def log(self, base: float | ComplexArg | None = None) -> ComplexI:
        """Logarithm."""
        import cmath

        from nu import FuncCallOp

        if base is not None:
            return ComplexI(FuncCallOp(cmath.log, self, base))
        return ComplexI(FuncCallOp(cmath.log, self))

    def sin(self) -> ComplexI:
        """Sine."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.sin, self))

    def cos(self) -> ComplexI:
        """Cosine."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.cos, self))

    def tan(self) -> ComplexI:
        """Tangent."""
        import cmath

        from nu import FuncCallOp

        return ComplexI(FuncCallOp(cmath.tan, self))

    # =========================================================================
    # EQUALITY (complex is equalable only, not comparable)
    # =========================================================================

    def eq(self, other: ComplexArg) -> BoolI:
        """Equal."""
        from nu import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: ComplexArg) -> BoolI:
        """Not equal."""
        from nu import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))


class ComplexI(_ComplexI, TypedNu[complex]):
    """Complex interface. Arithmetic + equality + component access."""
