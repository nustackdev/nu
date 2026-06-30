"""``fractions.Fraction`` as a Form: ``Fraction`` - exact rational arithmetic.

The name is ``Fraction`` to mirror ``from fractions import Fraction``, backed by
``fractions.Fraction`` (``from fractions import Fraction as _Fraction``). It is
the typed access surface for the stdlib type:

- **property reads** (``.numerator``, ``.denominator``) reuse core
  ``GetAttrQuery`` - a component is just an attribute read.
- **method calls** (``limit_denominator``, ``as_integer_ratio``) are named
  ``ScalarQueryFactory`` atoms in ``interactions`` (each binds the unbound
  ``Fraction`` method).
- **arithmetic** (``+`` ``-`` ``*`` ``/`` ``//`` ``%`` ``**`` and the unary
  ``-`` ``abs`` ``+``) reuses the core arithmetic atoms - Python performs the
  real rational op on the resolved values, the result is rewrapped as a
  ``Fraction``.
- **comparison** reuses the core comparison atoms.
- **constructors** are ``ScalarQueryFactory`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
"""

from __future__ import annotations

from fractions import Fraction as _Fraction
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from decimal import Decimal as _Decimal

    from nu.forms.collections import TupleForm
    from nu.forms.primitives import BoolForm, IntForm
    from nu.lang import Arg, FloatArg, IntArg, StrArg

    type FractionArg = Arg[_Fraction]
    type DecimalArg = Arg[_Decimal]


__all__ = ["Fraction"]


class Fraction(Form, TypedNu[_Fraction]):
    """``fractions.Fraction`` as a Form - an exact rational number.

    Named ``Fraction`` to mirror ``from fractions import Fraction``. Build one
    with ``Fraction.of(num, den)`` (or ``from_float`` / ``from_decimal`` /
    ``from_str``); read its parts as properties; combine with arithmetic and
    comparison operators.
    """

    # =========================================================================
    # CONSTRUCTORS (new atoms in interactions)
    # =========================================================================

    @classmethod
    def of(cls, numerator: IntArg, denominator: IntArg = 1) -> Fraction:
        """Build a fraction from numerator and denominator: ``Fraction(n, d)``."""
        from .interactions import FractionOf

        return Fraction(FractionOf(numerator, denominator))

    @classmethod
    def from_float(cls, value: FloatArg) -> Fraction:
        """The exact fraction equal to a float: ``Fraction.from_float(f)``."""
        from .interactions import FractionFromFloat

        return Fraction(FractionFromFloat(value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> Fraction:
        """The exact fraction equal to a Decimal: ``Fraction.from_decimal(d)``."""
        from .interactions import FractionFromDecimal

        return Fraction(FractionFromDecimal(value))

    @classmethod
    def from_str(cls, value: StrArg) -> Fraction:
        """Parse a fraction string: ``Fraction(s)`` (e.g. ``"3/4"``, ``"1.5"``)."""
        from .interactions import FractionFromStr

        return Fraction(FractionFromStr(value))

    # =========================================================================
    # COMPONENT READS (reuse core GetAttrQuery)
    # =========================================================================

    def numerator(self) -> IntForm:
        """The numerator (in lowest terms)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "numerator"))

    def denominator(self) -> IntForm:
        """The denominator (in lowest terms, always positive)."""
        from nu import IntForm
        from nu.core import GetAttrQuery

        return IntForm(GetAttrQuery(self, "denominator"))

    # =========================================================================
    # METHODS (factory atoms over unbound methods)
    # =========================================================================

    def limit_denominator(self, max_denominator: IntArg = 1_000_000) -> Fraction:
        """The closest fraction with denominator at most ``max_denominator``."""
        from .interactions import FractionLimitDenominator

        return Fraction(FractionLimitDenominator(self, max_denominator))

    def as_integer_ratio(self) -> TupleForm:
        """The ``(numerator, denominator)`` pair as a tuple."""
        from nu import TupleForm

        from .interactions import FractionAsIntegerRatio

        return TupleForm(FractionAsIntegerRatio(self))

    # =========================================================================
    # ARITHMETIC (reuse core atoms; Python does the real op)
    # =========================================================================

    def __add__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import AddQuery

        return Fraction(AddQuery(self, other))

    def __sub__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import SubQuery

        return Fraction(SubQuery(self, other))

    def __mul__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import MulQuery

        return Fraction(MulQuery(self, other))

    def __truediv__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import DivQuery

        return Fraction(DivQuery(self, other))

    def __floordiv__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import FloorDivQuery

        return Fraction(FloorDivQuery(self, other))

    def __mod__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import ModQuery

        return Fraction(ModQuery(self, other))

    def __pow__(self, other: IntArg) -> Fraction:
        from nu.core import PowQuery

        return Fraction(PowQuery(self, other))

    def __neg__(self) -> Fraction:
        from nu.core import NegQuery

        return Fraction(NegQuery(self))

    def __abs__(self) -> Fraction:
        from nu.core import AbsQuery

        return Fraction(AbsQuery(self))

    def __pos__(self) -> Fraction:
        from nu.core import PosQuery

        return Fraction(PosQuery(self))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: FractionArg | IntArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GtQuery

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: FractionArg | IntArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LtQuery

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: FractionArg | IntArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import GeQuery

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: FractionArg | IntArg) -> BoolForm:
        from nu import BoolForm
        from nu.core import LeQuery

        return BoolForm(LeQuery(self, other))

    def eq(self, other: FractionArg | IntArg) -> BoolForm:
        """Whether two fractions are equal."""
        from nu import BoolForm
        from nu.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def ne(self, other: FractionArg | IntArg) -> BoolForm:
        """Whether two fractions differ."""
        from nu import BoolForm
        from nu.core import NeQuery

        return BoolForm(NeQuery(self, other))
