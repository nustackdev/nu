"""decimal interactions - one ``host`` binding per host call.

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

from nu.factory import host


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

DecimalOf = host(lambda value: _Decimal(str(value)), name="DecimalOf")
DecimalFromFloat = host(_Decimal.from_float, name="DecimalFromFloat")

# --- decimal-returning methods ----------------------------------------------

DecimalQuantize = host(_Decimal.quantize, name="DecimalQuantize")
DecimalNormalize = host(_Decimal.normalize, name="DecimalNormalize")
DecimalToIntegralValue = host(_Decimal.to_integral_value, name="DecimalToIntegralValue")
DecimalSqrt = host(_Decimal.sqrt, name="DecimalSqrt")
DecimalExp = host(_Decimal.exp, name="DecimalExp")
DecimalLn = host(_Decimal.ln, name="DecimalLn")
DecimalLog10 = host(_Decimal.log10, name="DecimalLog10")
DecimalCompare = host(_Decimal.compare, name="DecimalCompare")
DecimalCopyAbs = host(_Decimal.copy_abs, name="DecimalCopyAbs")
DecimalCopyNegate = host(_Decimal.copy_negate, name="DecimalCopyNegate")

# --- other-typed methods ----------------------------------------------------

DecimalAdjusted = host(_Decimal.adjusted, name="DecimalAdjusted")
DecimalAsIntegerRatio = host(_Decimal.as_integer_ratio, name="DecimalAsIntegerRatio")

# --- predicate methods ------------------------------------------------------

DecimalIsFinite = host(_Decimal.is_finite, name="DecimalIsFinite")
DecimalIsInfinite = host(_Decimal.is_infinite, name="DecimalIsInfinite")
DecimalIsNan = host(_Decimal.is_nan, name="DecimalIsNan")
DecimalIsZero = host(_Decimal.is_zero, name="DecimalIsZero")
DecimalIsSigned = host(_Decimal.is_signed, name="DecimalIsSigned")
