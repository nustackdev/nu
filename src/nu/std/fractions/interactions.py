"""fractions interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind the class / its classmethods; methods bind the *unbound*
method (a plain callable whose first argument is the receiver, so
``f.limit_denominator(n)`` is ``Fraction.limit_denominator(f, n)``). Property
reads (``.numerator``, ``.denominator``) are not here - they reuse core
``GetAttrQuery`` from the Form. Arithmetic and comparison reuse the core atoms.

``FractionOf`` and ``FractionFromStr`` both bind the ``Fraction`` constructor:
``Fraction(num, den)`` (the two-argument literal) and ``Fraction(s)`` (a single
string) are the same callable with different arities.
"""

from __future__ import annotations

from fractions import Fraction as _Fraction

from nu.lang import ScalarQueryFactory


__all__ = [
    "FractionAsIntegerRatio",
    "FractionFromDecimal",
    "FractionFromFloat",
    "FractionFromStr",
    "FractionLimitDenominator",
    "FractionOf",
]


# --- constructors -----------------------------------------------------------

FractionOf = ScalarQueryFactory("FractionOf", _Fraction)
FractionFromStr = ScalarQueryFactory("FractionFromStr", _Fraction)
FractionFromFloat = ScalarQueryFactory("FractionFromFloat", _Fraction.from_float)
FractionFromDecimal = ScalarQueryFactory("FractionFromDecimal", _Fraction.from_decimal)

# --- methods ----------------------------------------------------------------

FractionLimitDenominator = ScalarQueryFactory(
    "FractionLimitDenominator", _Fraction.limit_denominator
)
FractionAsIntegerRatio = ScalarQueryFactory("FractionAsIntegerRatio", _Fraction.as_integer_ratio)
