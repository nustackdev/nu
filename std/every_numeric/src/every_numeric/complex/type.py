"""Complex Type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from term.ops import AddOp, DivOp, FuncCallOp, MethodCallOp, MulOp, PowOp, SubOp
from term.types import BaseType, EqualableBase, FloatType, NegatableBase
from term.typing import Sentinel

from every._abc import FloatArg, IntArg, StrArg, Term

from .args import ComplexArg


if TYPE_CHECKING:
    from term.types import TupleType


__all__ = [
    "ComplexType",
]


class ComplexType(
    EqualableBase["complex | ComplexType"],
    NegatableBase["ComplexType"],
    BaseType[complex | Sentinel],
):
    """Type representing a complex number.

    Supports complex arithmetic and component access.
    Stored as "real,imag" string for serialization.

    Note: Complex numbers are not orderable (no <, >, <=, >=).

    Example:
        >>> c = ComplexType.from_components(3, 4)
        >>> c.real()  # FloatType: 3.0
        >>> c.imag()  # FloatType: 4.0
        >>> abs(c)  # FloatType: 5.0
        >>> c.conjugate()  # ComplexType: 3-4j
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return ComplexType(operand)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        real: FloatArg = 0,
        imag: FloatArg = 0,
    ) -> ComplexType:
        """Create a ComplexType from real and imaginary parts.

        Args:
            real: Real part.
            imag: Imaginary part.

        Returns:
            ComplexType from components.

        Example:
            >>> ComplexType.from_components(3, 4)  # 3+4j
        """
        return cls(FuncCallOp(complex, real, imag))

    @classmethod
    def from_str(cls, value: StrArg) -> ComplexType:
        """Create a ComplexType from a string.

        Args:
            value: Complex number string (e.g., "3+4j", "(3+4j)").

        Returns:
            ComplexType from string.

        Example:
            >>> ComplexType.from_str("3+4j")
        """
        return cls(FuncCallOp(complex, value))

    @classmethod
    def from_polar(
        cls,
        r: FloatArg,
        phi: FloatArg,
    ) -> ComplexType:
        """Create a ComplexType from polar coordinates.

        Args:
            r: Magnitude (radius).
            phi: Phase angle in radians.

        Returns:
            ComplexType from polar form.

        Example:
            >>> import math
            >>> ComplexType.from_polar(5, math.atan2(4, 3))  # 3+4j
        """
        import cmath

        return cls(FuncCallOp(cmath.rect, r, phi))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def real(self) -> FloatType:
        """Get the real part.

        Returns:
            FloatType containing the real part.
        """
        return FloatType(FuncCallOp(getattr, self, "real"))

    def imag(self) -> FloatType:
        """Get the imaginary part.

        Returns:
            FloatType containing the imaginary part.
        """
        return FloatType(FuncCallOp(getattr, self, "imag"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: ComplexArg) -> ComplexType:
        """Add complex numbers.

        Args:
            other: Value to add.

        Returns:
            Sum as ComplexType.
        """
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(AddOp(self, other))

    def __radd__(self, other: ComplexArg | IntArg | FloatArg) -> ComplexType:
        """Right add."""
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(AddOp(other, self))

    def __sub__(self, other: ComplexArg) -> ComplexType:
        """Subtract complex numbers.

        Args:
            other: Value to subtract.

        Returns:
            Difference as ComplexType.
        """
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(SubOp(self, other))

    def __rsub__(self, other: ComplexArg | IntArg | FloatArg) -> ComplexType:
        """Right subtract."""
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(SubOp(other, self))

    def __mul__(self, other: ComplexArg) -> ComplexType:
        """Multiply complex numbers.

        Args:
            other: Value to multiply.

        Returns:
            Product as ComplexType.
        """
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(MulOp(self, other))

    def __rmul__(self, other: ComplexArg | IntArg | FloatArg) -> ComplexType:
        """Right multiply."""
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(MulOp(other, self))

    def __truediv__(self, other: ComplexArg) -> ComplexType:
        """Divide complex numbers.

        Args:
            other: Divisor.

        Returns:
            Quotient as ComplexType.
        """
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(DivOp(self, other))

    def __rtruediv__(self, other: ComplexArg | IntArg | FloatArg) -> ComplexType:
        """Right divide."""
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(DivOp(other, self))

    def __pow__(self, other: ComplexArg) -> ComplexType:
        """Raise to power.

        Args:
            other: Exponent.

        Returns:
            Result as ComplexType.
        """
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(PowOp(self, other))

    def __rpow__(self, other: ComplexArg | IntArg | FloatArg) -> ComplexType:
        """Right power."""
        if isinstance(other, complex):
            other = ComplexType(other)
        return ComplexType(PowOp(other, self))

    # FIXME: fix type hint (negatable base incorrectly assumes return value of abs to always be Self).
    def __abs__(self) -> FloatType:
        """Get magnitude (absolute value).

        Returns:
            FloatType containing the magnitude.
        """
        return FloatType(FuncCallOp(abs, self))

    # =========================================================================
    # COMPLEX OPERATIONS
    # =========================================================================

    def conjugate(self) -> ComplexType:
        """Get the complex conjugate.

        Returns:
            ComplexType with negated imaginary part.
        """
        return ComplexType(MethodCallOp(self, "conjugate"))

    def phase(self) -> FloatType:
        """Get the phase angle in radians.

        Returns:
            FloatType containing the phase.
        """
        import cmath

        return FloatType(FuncCallOp(cmath.phase, self))

    def polar(self) -> TupleType:
        """Convert to polar coordinates (r, phi).

        Returns:
            TupleType containing (magnitude, phase).
        """
        import cmath

        from term.types import TupleType

        return TupleType(FuncCallOp(cmath.polar, self))

    # =========================================================================
    # MATHEMATICAL FUNCTIONS
    # =========================================================================

    def sqrt(self) -> ComplexType:
        """Square root.

        Returns:
            Square root as ComplexType.
        """
        import cmath

        return ComplexType(FuncCallOp(cmath.sqrt, self))

    def exp(self) -> ComplexType:
        """Exponential (e^self).

        Returns:
            Exponential as ComplexType.
        """
        import cmath

        return ComplexType(FuncCallOp(cmath.exp, self))

    def log(self, base: FloatArg | ComplexArg | None = None) -> ComplexType:
        """Logarithm.

        Args:
            base: Log base (natural log if None).

        Returns:
            Logarithm as ComplexType.
        """
        import cmath

        if base is not None:
            return ComplexType(FuncCallOp(cmath.log, self, base))
        return ComplexType(FuncCallOp(cmath.log, self))

    def sin(self) -> ComplexType:
        """Sine.

        Returns:
            Sine as ComplexType.
        """
        import cmath

        return ComplexType(FuncCallOp(cmath.sin, self))

    def cos(self) -> ComplexType:
        """Cosine.

        Returns:
            Cosine as ComplexType.
        """
        import cmath

        return ComplexType(FuncCallOp(cmath.cos, self))

    def tan(self) -> ComplexType:
        """Tangent.

        Returns:
            Tangent as ComplexType.
        """
        import cmath

        return ComplexType(FuncCallOp(cmath.tan, self))
