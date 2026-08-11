"""fractions interactions - one ``host`` binding per host call.

Constructors bind the class / its classmethods; methods bind the *unbound*
method (a plain callable whose first argument is the receiver, so
``f.limit_denominator(n)`` is ``Fraction.limit_denominator(f, n)``). Property
reads (``.numerator``, ``.denominator``) are not here - they reuse core
``GetAttr`` from the Form. Arithmetic and comparison reuse the core atoms.

``FractionOf`` and ``FractionFromStr`` both bind the ``Fraction`` constructor:
``Fraction(num, den)`` (the two-argument literal) and ``Fraction(s)`` (a single
string) are the same callable with different arities.
"""

from __future__ import annotations

from fractions import Fraction as _Fraction

from nu.factory import host


__all__ = [
    "FractionAsIntegerRatio",
    "FractionFromDecimal",
    "FractionFromFloat",
    "FractionFromStr",
    "FractionLimitDenominator",
    "FractionOf",
]


# --- constructors -----------------------------------------------------------

FractionOf = host(_Fraction, name="FractionOf")
FractionFromStr = host(_Fraction, name="FractionFromStr")
FractionFromFloat = host(_Fraction.from_float, name="FractionFromFloat")
FractionFromDecimal = host(_Fraction.from_decimal, name="FractionFromDecimal")

# --- methods ----------------------------------------------------------------

FractionLimitDenominator = host(_Fraction.limit_denominator, name="FractionLimitDenominator")
FractionAsIntegerRatio = host(_Fraction.as_integer_ratio, name="FractionAsIntegerRatio")
