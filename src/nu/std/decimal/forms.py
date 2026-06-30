"""``decimal.Decimal`` as a Form: ``Decimal`` - arbitrary-precision arithmetic.

The name is ``Decimal`` (capitalized) to mirror ``from decimal import Decimal``;
it is backed by ``decimal.Decimal`` (``from decimal import Decimal as _Decimal``)
and is the typed access surface for that type:

- **constructors** are ``ScalarQueryFactory`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
  ``of`` coerces its argument through ``str`` so the value is exact (``of("0.1")``
  is ``Decimal('0.1')``, never the binary float ``0.1``).
- **arithmetic** (``+`` ``-`` ``*`` ``/`` ``//`` ``%`` ``**`` ``-x`` ``abs`` ``+x``)
  reuses the core arithmetic atoms - Python performs the real ``Decimal`` op on
  the resolved values, so precision is preserved.
- **comparison** reuses the core comparison atoms.
- **method calls** (``quantize``, ``sqrt``, ``compare`` ...) are named
  ``ScalarQueryFactory`` atoms in ``interactions`` (each binds the unbound
  ``Decimal`` method) and return the right Form.

Module-level helpers and contexts (``getcontext``, ``localcontext``,
``ROUND_*`` ...) are out of scope - this models the ``Decimal`` type only.
"""

from __future__ import annotations

from decimal import Decimal as _Decimal
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.collections import TupleForm
    from nu.forms.primitives import BoolForm, IntForm
    from nu.lang import Arg, FloatArg, IntArg, StrArg

    type DecimalArg = Arg[_Decimal]


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
        from nu.core import AddQuery

        return Decimal(AddQuery(self, other))

    def __sub__(self, other: DecimalArg) -> Decimal:
        from nu.core import SubQuery

        return Decimal(SubQuery(self, other))

    def __mul__(self, other: DecimalArg) -> Decimal:
        from nu.core import MulQuery

        return Decimal(MulQuery(self, other))

    def __truediv__(self, other: DecimalArg) -> Decimal:
        from nu.core import DivQuery

        return Decimal(DivQuery(self, other))

    def __floordiv__(self, other: DecimalArg) -> Decimal:
        from nu.core import FloorDivQuery

        return Decimal(FloorDivQuery(self, other))

    def __mod__(self, other: DecimalArg) -> Decimal:
        from nu.core import ModQuery

        return Decimal(ModQuery(self, other))

    def __pow__(self, other: DecimalArg | IntArg) -> Decimal:
        from nu.core import PowQuery

        return Decimal(PowQuery(self, other))

    def __neg__(self) -> Decimal:
        from nu.core import NegQuery

        return Decimal(NegQuery(self))

    def __abs__(self) -> Decimal:
        from nu.core import AbsQuery

        return Decimal(AbsQuery(self))

    def __pos__(self) -> Decimal:
        from nu.core import PosQuery

        return Decimal(PosQuery(self))

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

    def adjusted(self) -> IntForm:
        """The adjusted exponent after shifting out the coefficient's digits."""
        from nu import IntForm

        from .interactions import DecimalAdjusted

        return IntForm(DecimalAdjusted(self))

    def as_integer_ratio(self) -> TupleForm:
        """The exact value as a ``(numerator, denominator)`` pair of ints."""
        from nu import TupleForm

        from .interactions import DecimalAsIntegerRatio

        return TupleForm(DecimalAsIntegerRatio(self))

    # =========================================================================
    # PREDICATES (factory atoms)
    # =========================================================================

    def is_finite(self) -> BoolForm:
        """Whether the value is finite (not infinite, not NaN)."""
        from nu import BoolForm

        from .interactions import DecimalIsFinite

        return BoolForm(DecimalIsFinite(self))

    def is_infinite(self) -> BoolForm:
        """Whether the value is positive or negative infinity."""
        from nu import BoolForm

        from .interactions import DecimalIsInfinite

        return BoolForm(DecimalIsInfinite(self))

    def is_nan(self) -> BoolForm:
        """Whether the value is a NaN (quiet or signaling)."""
        from nu import BoolForm

        from .interactions import DecimalIsNan

        return BoolForm(DecimalIsNan(self))

    def is_zero(self) -> BoolForm:
        """Whether the value is zero (positive or negative)."""
        from nu import BoolForm

        from .interactions import DecimalIsZero

        return BoolForm(DecimalIsZero(self))

    def is_signed(self) -> BoolForm:
        """Whether the sign bit is set (negative, including ``-0``)."""
        from nu import BoolForm

        from .interactions import DecimalIsSigned

        return BoolForm(DecimalIsSigned(self))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: DecimalArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GtQuery

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: DecimalArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LtQuery

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: DecimalArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GeQuery

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: DecimalArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LeQuery

        return BoolForm(LeQuery(self, other))

    def eq(self, other: DecimalArg) -> BoolForm:
        """Whether two decimals are equal in value."""
        from nu import BoolForm
        from nu.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def ne(self, other: DecimalArg) -> BoolForm:
        """Whether two decimals differ in value."""
        from nu import BoolForm
        from nu.core import NeQuery

        return BoolForm(NeQuery(self, other))
