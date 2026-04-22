"""ComplexI - complex number interface.

ComplexI = TypedNu[complex] + arithmetic + equality + component access.
Complex numbers are not orderable (no <, >, <=, >=).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


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
        from nu import FuncCall

        return ComplexI(FuncCall(complex, real, imag))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> ComplexI:
        """Create a ComplexI from a string."""
        from nu import FuncCall

        return ComplexI(FuncCall(complex, value))

    @classmethod
    def from_polar(cls, r: float | Nu[float], phi: float | Nu[float]) -> ComplexI:
        """Create a ComplexI from polar coordinates."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.rect, r, phi))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def real(self) -> FloatI:
        """Get the real part."""
        from nu import FuncCall
        from nu.primitives import FloatI

        return FloatI(FuncCall(getattr, self, "real"))

    def imag(self) -> FloatI:
        """Get the imaginary part."""
        from nu import FuncCall
        from nu.primitives import FloatI

        return FloatI(FuncCall(getattr, self, "imag"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: ComplexArg) -> ComplexI:
        """Add complex numbers."""
        from nu import Add

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Add(self, other))

    def __radd__(self, other: complex | int | float) -> ComplexI:
        """Right add."""
        from nu import Add

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Add(other, self))

    def __sub__(self, other: ComplexArg) -> ComplexI:
        """Subtract complex numbers."""
        from nu import Sub

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Sub(self, other))

    def __rsub__(self, other: complex | int | float) -> ComplexI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Sub(other, self))

    def __mul__(self, other: ComplexArg) -> ComplexI:
        """Multiply complex numbers."""
        from nu import Mul

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Mul(self, other))

    def __rmul__(self, other: complex | int | float) -> ComplexI:
        """Right multiply."""
        from nu import Mul

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Mul(other, self))

    def __truediv__(self, other: ComplexArg) -> ComplexI:
        """Divide complex numbers."""
        from nu import Div

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Div(self, other))

    def __rtruediv__(self, other: complex | int | float) -> ComplexI:
        """Right divide."""
        from nu import Div

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Div(other, self))

    def __pow__(self, other: ComplexArg) -> ComplexI:
        """Raise to power."""
        from nu import Pow

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Pow(self, other))

    def __rpow__(self, other: complex | int | float) -> ComplexI:
        """Right power."""
        from nu import Pow

        if isinstance(other, complex):
            other = ComplexI(other)
        return ComplexI(Pow(other, self))

    def __neg__(self) -> ComplexI:
        """Negate."""
        from nu import Neg

        return ComplexI(Neg(self))

    def __abs__(self) -> FloatI:
        """Get magnitude (absolute value)."""
        from nu import FuncCall
        from nu.primitives import FloatI

        return FloatI(FuncCall(abs, self))

    # =========================================================================
    # COMPLEX OPERATIONS
    # =========================================================================

    def conjugate(self) -> ComplexI:
        """Get the complex conjugate."""
        from nu import MethodCall

        return ComplexI(MethodCall(self, "conjugate"))

    def phase(self) -> FloatI:
        """Get the phase angle in radians."""
        import cmath

        from nu import FuncCall
        from nu.primitives import FloatI

        return FloatI(FuncCall(cmath.phase, self))

    def polar(self) -> TupleI:
        """Get polar coordinates (r, phi)."""
        import cmath

        from nu import FuncCall
        from nu.collections import TupleI

        return TupleI(FuncCall(cmath.polar, self))

    # =========================================================================
    # MATHEMATICAL FUNCTIONS
    # =========================================================================

    def sqrt(self) -> ComplexI:
        """Square root."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.sqrt, self))

    def exp(self) -> ComplexI:
        """Exponential (e^self)."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.exp, self))

    def log(self, base: float | ComplexArg | None = None) -> ComplexI:
        """Logarithm."""
        import cmath

        from nu import FuncCall

        if base is not None:
            return ComplexI(FuncCall(cmath.log, self, base))
        return ComplexI(FuncCall(cmath.log, self))

    def sin(self) -> ComplexI:
        """Sine."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.sin, self))

    def cos(self) -> ComplexI:
        """Cosine."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.cos, self))

    def tan(self) -> ComplexI:
        """Tangent."""
        import cmath

        from nu import FuncCall

        return ComplexI(FuncCall(cmath.tan, self))

    # =========================================================================
    # EQUALITY (complex is equalable only, not comparable)
    # =========================================================================

    def eq(self, other: ComplexArg) -> BoolI:
        """Equal."""
        from nu import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: ComplexArg) -> BoolI:
        """Not equal."""
        from nu import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))


class ComplexI(_ComplexI, TypedNu[complex]):
    """Complex interface. Arithmetic + equality + component access."""
