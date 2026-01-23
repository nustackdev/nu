"""Complex ref base for complex number arithmetic.

ComplexRefBase = RefBase[complex] + Equalable + arithmetic operations.
Note: Complex numbers are not orderable (no <, >, <=, >=).
Returns concrete py types (ComplexRef, FloatRef).
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Equalable


if TYPE_CHECKING:
    from every import Term
    from everybase.py import FloatRef, TupleRef

    from .args import ComplexArg
    from .py.refs import ComplexRef


__all__ = [
    "ComplexRefBase",
]


class ComplexRefBase(
    Equalable["complex | ComplexRef"],
    RefBase[complex],
    ABC,
):
    """Abstract base for complex number refs.

    Supports complex arithmetic and component access.
    Stored as "real,imag" string for serialization.

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
    ) -> ComplexRef:
        """Create a ComplexRef from real and imaginary parts."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(complex, real, imag))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> ComplexRef:
        """Create a ComplexRef from a string."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(complex, value))

    @classmethod
    def from_polar(cls, r: float | Term[float], phi: float | Term[float]) -> ComplexRef:
        """Create a ComplexRef from polar coordinates."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.rect, r, phi))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def real(self) -> FloatRef:
        """Get the real part."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import FloatRef

        return FloatRef(FuncCallOp(getattr, self, "real"))

    def imag(self) -> FloatRef:
        """Get the imaginary part."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import FloatRef

        return FloatRef(FuncCallOp(getattr, self, "imag"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: ComplexArg) -> ComplexRef:
        """Add complex numbers."""
        from everybase.morphisms import AddOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(AddOp(self, other))

    def __radd__(self, other: complex | int | float) -> ComplexRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(AddOp(other, self))

    def __sub__(self, other: ComplexArg) -> ComplexRef:
        """Subtract complex numbers."""
        from everybase.morphisms import SubOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(SubOp(self, other))

    def __rsub__(self, other: complex | int | float) -> ComplexRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(SubOp(other, self))

    def __mul__(self, other: ComplexArg) -> ComplexRef:
        """Multiply complex numbers."""
        from everybase.morphisms import MulOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(MulOp(self, other))

    def __rmul__(self, other: complex | int | float) -> ComplexRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(MulOp(other, self))

    def __truediv__(self, other: ComplexArg) -> ComplexRef:
        """Divide complex numbers."""
        from everybase.morphisms import DivOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(DivOp(self, other))

    def __rtruediv__(self, other: complex | int | float) -> ComplexRef:
        """Right divide."""
        from everybase.morphisms import DivOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(DivOp(other, self))

    def __pow__(self, other: ComplexArg) -> ComplexRef:
        """Raise to power."""
        from everybase.morphisms import PowOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(PowOp(self, other))

    def __rpow__(self, other: complex | int | float) -> ComplexRef:
        """Right power."""
        from everybase.morphisms import PowOp

        from .py.refs import ComplexRef

        if isinstance(other, complex):
            other = ComplexRef(other)
        return ComplexRef(PowOp(other, self))

    def __neg__(self) -> ComplexRef:
        """Negate."""
        from everybase.morphisms import NegOp

        from .py.refs import ComplexRef

        return ComplexRef(NegOp(self))

    def __abs__(self) -> FloatRef:
        """Get magnitude (absolute value)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import FloatRef

        return FloatRef(FuncCallOp(abs, self))

    # =========================================================================
    # COMPLEX OPERATIONS
    # =========================================================================

    def conjugate(self) -> ComplexRef:
        """Get the complex conjugate."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import ComplexRef

        return ComplexRef(MethodCallOp(self, "conjugate"))

    def phase(self) -> FloatRef:
        """Get the phase angle in radians."""
        import cmath

        from everybase.morphisms import FuncCallOp
        from everybase.py import FloatRef

        return FloatRef(FuncCallOp(cmath.phase, self))

    def polar(self) -> TupleRef:
        """Get polar coordinates (r, phi)."""
        import cmath

        from everybase.morphisms import FuncCallOp
        from everybase.py import TupleRef

        return TupleRef(FuncCallOp(cmath.polar, self))

    # =========================================================================
    # MATHEMATICAL FUNCTIONS
    # =========================================================================

    def sqrt(self) -> ComplexRef:
        """Square root."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.sqrt, self))

    def exp(self) -> ComplexRef:
        """Exponential (e^self)."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.exp, self))

    def log(self, base: float | ComplexArg | None = None) -> ComplexRef:
        """Logarithm."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        if base is not None:
            return ComplexRef(FuncCallOp(cmath.log, self, base))
        return ComplexRef(FuncCallOp(cmath.log, self))

    def sin(self) -> ComplexRef:
        """Sine."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.sin, self))

    def cos(self) -> ComplexRef:
        """Cosine."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.cos, self))

    def tan(self) -> ComplexRef:
        """Tangent."""
        import cmath

        from everybase.morphisms import FuncCallOp

        from .py.refs import ComplexRef

        return ComplexRef(FuncCallOp(cmath.tan, self))
