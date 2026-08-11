"""``fractions.Fraction`` as a Form: ``Fraction`` - exact rational arithmetic.

The name is ``Fraction`` to mirror ``from fractions import Fraction``, backed by
``fractions.Fraction`` (``from fractions import Fraction as _Fraction``). It is
the typed access surface for the stdlib type:

- **property reads** (``.numerator``, ``.denominator``) reuse core
  ``GetAttr`` - a component is just an attribute read.
- **method calls** (``limit_denominator``, ``as_integer_ratio``) are named
  ``host`` atoms in ``interactions`` (each binds the unbound
  ``Fraction`` method).
- **arithmetic** (``+`` ``-`` ``*`` ``/`` ``//`` ``%`` ``**`` and the unary
  ``-`` ``abs`` ``+``) reuses the core arithmetic atoms - Python performs the
  real rational op on the resolved values, the result is rewrapped as a
  ``Fraction``.
- **comparison** reuses the core comparison atoms.
- **constructors** are ``host`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
"""

from __future__ import annotations

from fractions import Fraction as _Fraction
from typing import TYPE_CHECKING, TypeAlias

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from decimal import Decimal as _Decimal

    from nu.forms.collections import Tuple
    from nu.forms.primitives import Bool, Int
    from nu.lang import Arg, FloatArg, IntArg, StrArg

    FractionArg: TypeAlias = "Arg[_Fraction]"
    DecimalArg: TypeAlias = "Arg[_Decimal]"


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
    # COMPONENT READS (reuse core GetAttr)
    # =========================================================================

    def numerator(self) -> Int:
        """The numerator (in lowest terms)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "numerator"))

    def denominator(self) -> Int:
        """The denominator (in lowest terms, always positive)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "denominator"))

    # =========================================================================
    # METHODS (factory atoms over unbound methods)
    # =========================================================================

    def limit_denominator(self, max_denominator: IntArg = 1_000_000) -> Fraction:
        """The closest fraction with denominator at most ``max_denominator``."""
        from .interactions import FractionLimitDenominator

        return Fraction(FractionLimitDenominator(self, max_denominator))

    def as_integer_ratio(self) -> Tuple:
        """The ``(numerator, denominator)`` pair as a tuple."""
        from nu.forms import Tuple

        from .interactions import FractionAsIntegerRatio

        return Tuple(FractionAsIntegerRatio(self))

    # =========================================================================
    # ARITHMETIC (reuse core atoms; Python does the real op)
    # =========================================================================

    def __add__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import Add

        return Fraction(Add(self, other))

    def __sub__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import Sub

        return Fraction(Sub(self, other))

    def __mul__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import Mul

        return Fraction(Mul(self, other))

    def __truediv__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import Div

        return Fraction(Div(self, other))

    def __floordiv__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import FloorDiv

        return Fraction(FloorDiv(self, other))

    def __mod__(self, other: FractionArg | IntArg) -> Fraction:
        from nu.core import Mod

        return Fraction(Mod(self, other))

    def __pow__(self, other: IntArg) -> Fraction:
        from nu.core import Pow

        return Fraction(Pow(self, other))

    def __neg__(self) -> Fraction:
        from nu.core import Neg

        return Fraction(Neg(self))

    def __abs__(self) -> Fraction:
        from nu.core import Abs

        return Fraction(Abs(self))

    def __pos__(self) -> Fraction:
        from nu.core import Pos

        return Fraction(Pos(self))

    # =========================================================================
    # COMPARISON (reuse core comparison atoms)
    # =========================================================================

    def __gt__(self, other: FractionArg | IntArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: FractionArg | IntArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: FractionArg | IntArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: FractionArg | IntArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: FractionArg | IntArg) -> Bool:
        """Whether two fractions are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: FractionArg | IntArg) -> Bool:
        """Whether two fractions differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
