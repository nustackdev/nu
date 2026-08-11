"""``decimal.Decimal`` as a Form: ``Decimal`` - arbitrary-precision arithmetic.

The name is ``Decimal`` (capitalized) to mirror ``from decimal import Decimal``;
it is backed by ``decimal.Decimal`` (``from decimal import Decimal as _Decimal``)
and is the typed access surface for that type:

- **constructors** are ``host`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
  ``of`` coerces its argument through ``str`` so the value is exact (``of("0.1")``
  is ``Decimal('0.1')``, never the binary float ``0.1``).
- **arithmetic** (``+`` ``-`` ``*`` ``/`` ``//`` ``%`` ``**`` ``-x`` ``abs`` ``+x``)
  reuses the core arithmetic atoms - Python performs the real ``Decimal`` op on
  the resolved values, so precision is preserved.
- **comparison** reuses the core comparison atoms.
- **method calls** (``quantize``, ``sqrt``, ``compare`` ...) are named
  ``host`` atoms in ``interactions`` (each binds the unbound
  ``Decimal`` method) and return the right Form.

Module-level helpers and contexts (``getcontext``, ``localcontext``,
``ROUND_*`` ...) are out of scope - this models the ``Decimal`` type only.
"""

from __future__ import annotations

from decimal import Decimal as _Decimal
from typing import TYPE_CHECKING, TypeAlias

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.collections import Tuple
    from nu.forms.primitives import Bool, Int
    from nu.lang import Arg, FloatArg, IntArg, StrArg

    DecimalArg: TypeAlias = "Arg[_Decimal]"


__all__ = ["Decimal"]


class Decimal(Form, TypedNu[_Decimal]):
    """``decimal.Decimal`` as a Form - exact, arbitrary-precision arithmetic.

    Build one with ``Decimal.of(...)`` (string or int, coerced exactly) or
    ``Decimal.from_float(...)``; combine with the arithmetic operators; refine
    with the method calls. Python does the real ``Decimal`` op on the resolved
    values, so ``Decimal.of("0.1") + Decimal.of("0.2")`` is exactly
    ``Decimal('0.3')``.
    """

    # =========================================================================
    # CONSTRUCTORS (new atoms in interactions)
    # =========================================================================

    @classmethod
    def of(cls, value: StrArg | IntArg) -> Decimal:
        """Build a decimal from a string or int, exactly: ``Decimal(str(value))``."""
        from .interactions import DecimalOf

        return Decimal(DecimalOf(value))

    @classmethod
    def from_float(cls, value: FloatArg) -> Decimal:
        """From a binary float: ``Decimal.from_float(f)`` (carries float error)."""
        from .interactions import DecimalFromFloat

        return Decimal(DecimalFromFloat(value))

    # =========================================================================
    # ARITHMETIC (reuse core atoms; Python does the real Decimal op)
    # =========================================================================

    def __add__(self, other: DecimalArg) -> Decimal:
        from nu.core import Add

        return Decimal(Add(self, other))

    def __sub__(self, other: DecimalArg) -> Decimal:
        from nu.core import Sub

        return Decimal(Sub(self, other))

    def __mul__(self, other: DecimalArg) -> Decimal:
        from nu.core import Mul

        return Decimal(Mul(self, other))

    def __truediv__(self, other: DecimalArg) -> Decimal:
        from nu.core import Div

        return Decimal(Div(self, other))

    def __floordiv__(self, other: DecimalArg) -> Decimal:
        from nu.core import FloorDiv

        return Decimal(FloorDiv(self, other))

    def __mod__(self, other: DecimalArg) -> Decimal:
        from nu.core import Mod

        return Decimal(Mod(self, other))

    def __pow__(self, other: DecimalArg | IntArg) -> Decimal:
        from nu.core import Pow

        return Decimal(Pow(self, other))

    def __neg__(self) -> Decimal:
        from nu.core import Neg

        return Decimal(Neg(self))

    def __abs__(self) -> Decimal:
        from nu.core import Abs

        return Decimal(Abs(self))

    def __pos__(self) -> Decimal:
        from nu.core import Pos

        return Decimal(Pos(self))

    # =========================================================================
    # DECIMAL-RETURNING METHODS (factory atoms over unbound methods)
    # =========================================================================

    def quantize(self, exp: DecimalArg) -> Decimal:
        """Round to the exponent of ``exp`` (e.g. ``Decimal.of("0.01")``)."""
        from .interactions import DecimalQuantize

        return Decimal(DecimalQuantize(self, exp))

    def normalize(self) -> Decimal:
        """A canonical form with trailing zeros removed."""
        from .interactions import DecimalNormalize

        return Decimal(DecimalNormalize(self))

    def to_integral_value(self) -> Decimal:
        """The value rounded to the nearest integer, kept as a ``Decimal``."""
        from .interactions import DecimalToIntegralValue

        return Decimal(DecimalToIntegralValue(self))

    def sqrt(self) -> Decimal:
        """The square root."""
        from .interactions import DecimalSqrt

        return Decimal(DecimalSqrt(self))

    def exp(self) -> Decimal:
        """The exponential, ``e ** self``."""
        from .interactions import DecimalExp

        return Decimal(DecimalExp(self))

    def ln(self) -> Decimal:
        """The natural logarithm."""
        from .interactions import DecimalLn

        return Decimal(DecimalLn(self))

    def log10(self) -> Decimal:
        """The base-10 logarithm."""
        from .interactions import DecimalLog10

        return Decimal(DecimalLog10(self))

    def compare(self, other: DecimalArg) -> Decimal:
        """``Decimal('-1')`` / ``'0'`` / ``'1'`` for ``self`` <, ==, > ``other``."""
        from .interactions import DecimalCompare

        return Decimal(DecimalCompare(self, other))

    def copy_abs(self) -> Decimal:
        """The absolute value (context-free, no rounding)."""
        from .interactions import DecimalCopyAbs

        return Decimal(DecimalCopyAbs(self))

    def copy_negate(self) -> Decimal:
        """The negation (context-free, no rounding)."""
        from .interactions import DecimalCopyNegate

        return Decimal(DecimalCopyNegate(self))

    # =========================================================================
    # OTHER-TYPED METHODS (factory atoms)
    # =========================================================================

    def adjusted(self) -> Int:
        """The adjusted exponent after shifting out the coefficient's digits."""
        from nu.forms import Int

        from .interactions import DecimalAdjusted

        return Int(DecimalAdjusted(self))

    def as_integer_ratio(self) -> Tuple:
        """The exact value as a ``(numerator, denominator)`` pair of ints."""
        from nu.forms import Tuple

        from .interactions import DecimalAsIntegerRatio

        return Tuple(DecimalAsIntegerRatio(self))

    # =========================================================================
    # PREDICATES (factory atoms)
    # =========================================================================

    def is_finite(self) -> Bool:
        """Whether the value is finite (not infinite, not NaN)."""
        from nu.forms import Bool

        from .interactions import DecimalIsFinite

        return Bool(DecimalIsFinite(self))

    def is_infinite(self) -> Bool:
        """Whether the value is positive or negative infinity."""
        from nu.forms import Bool

        from .interactions import DecimalIsInfinite

        return Bool(DecimalIsInfinite(self))

    def is_nan(self) -> Bool:
        """Whether the value is a NaN (quiet or signaling)."""
        from nu.forms import Bool

        from .interactions import DecimalIsNan

        return Bool(DecimalIsNan(self))

    def is_zero(self) -> Bool:
        """Whether the value is zero (positive or negative)."""
        from nu.forms import Bool

        from .interactions import DecimalIsZero

        return Bool(DecimalIsZero(self))

    def is_signed(self) -> Bool:
        """Whether the sign bit is set (negative, including ``-0``)."""
        from nu.forms import Bool

        from .interactions import DecimalIsSigned

        return Bool(DecimalIsSigned(self))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: DecimalArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: DecimalArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: DecimalArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: DecimalArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: DecimalArg) -> Bool:
        """Whether two decimals are equal in value."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: DecimalArg) -> Bool:
        """Whether two decimals differ in value."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
