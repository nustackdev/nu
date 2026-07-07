"""decimal interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind the class / classmethod; methods bind the *unbound* method (a
plain callable whose first argument is the receiver, so ``d.sqrt()`` is
``Decimal.sqrt(d)``). Arithmetic and comparison are not here - they reuse the
core atoms.

``DecimalOf`` coerces its argument through ``str`` first, so ``DecimalOf("0.1")``
and ``DecimalOf(0)`` build exact values (a bare ``Decimal(0.1)`` would carry the
binary-float error). ``DecimalFromFloat`` keeps that float error on purpose - it
mirrors ``Decimal.from_float``.
"""

from __future__ import annotations

from decimal import Decimal as _Decimal

from nu.factory import ScalarQueryFactory


__all__ = [
    "DecimalAdjusted",
    "DecimalAsIntegerRatio",
    "DecimalCompare",
    "DecimalCopyAbs",
    "DecimalCopyNegate",
    "DecimalExp",
    "DecimalFromFloat",
    "DecimalIsFinite",
    "DecimalIsInfinite",
    "DecimalIsNan",
    "DecimalIsSigned",
    "DecimalIsZero",
    "DecimalLn",
    "DecimalLog10",
    "DecimalNormalize",
    "DecimalOf",
    "DecimalQuantize",
    "DecimalSqrt",
    "DecimalToIntegralValue",
]


# --- constructors -----------------------------------------------------------

DecimalOf = ScalarQueryFactory("DecimalOf", lambda value: _Decimal(str(value)))
DecimalFromFloat = ScalarQueryFactory("DecimalFromFloat", _Decimal.from_float)

# --- decimal-returning methods ----------------------------------------------

DecimalQuantize = ScalarQueryFactory("DecimalQuantize", _Decimal.quantize)
DecimalNormalize = ScalarQueryFactory("DecimalNormalize", _Decimal.normalize)
DecimalToIntegralValue = ScalarQueryFactory("DecimalToIntegralValue", _Decimal.to_integral_value)
DecimalSqrt = ScalarQueryFactory("DecimalSqrt", _Decimal.sqrt)
DecimalExp = ScalarQueryFactory("DecimalExp", _Decimal.exp)
DecimalLn = ScalarQueryFactory("DecimalLn", _Decimal.ln)
DecimalLog10 = ScalarQueryFactory("DecimalLog10", _Decimal.log10)
DecimalCompare = ScalarQueryFactory("DecimalCompare", _Decimal.compare)
DecimalCopyAbs = ScalarQueryFactory("DecimalCopyAbs", _Decimal.copy_abs)
DecimalCopyNegate = ScalarQueryFactory("DecimalCopyNegate", _Decimal.copy_negate)

# --- other-typed methods ----------------------------------------------------

DecimalAdjusted = ScalarQueryFactory("DecimalAdjusted", _Decimal.adjusted)
DecimalAsIntegerRatio = ScalarQueryFactory("DecimalAsIntegerRatio", _Decimal.as_integer_ratio)

# --- predicate methods ------------------------------------------------------

DecimalIsFinite = ScalarQueryFactory("DecimalIsFinite", _Decimal.is_finite)
DecimalIsInfinite = ScalarQueryFactory("DecimalIsInfinite", _Decimal.is_infinite)
DecimalIsNan = ScalarQueryFactory("DecimalIsNan", _Decimal.is_nan)
DecimalIsZero = ScalarQueryFactory("DecimalIsZero", _Decimal.is_zero)
DecimalIsSigned = ScalarQueryFactory("DecimalIsSigned", _Decimal.is_signed)
