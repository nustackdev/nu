"""math interactions - one ``ScalarQueryFactory`` binding per host call.

``math`` is a function module: no central class, just free functions over
floats and ints. Core can't compute ``sqrt``/``sin``/etc., so each one is a new
atom bound straight to the ``math.*`` callable. Constants (``pi``, ``e``, ...)
are plain values, so they need no atom - they ride on ``LiteralQuery`` in
``functions``.

Every binding here is pure (no clock, no randomness), so a future
constant-folding pass may fold any of them freely.
"""

from __future__ import annotations

import math

from nu.lang import ScalarQueryFactory


__all__ = [
    "MathAcos",
    "MathAsin",
    "MathAtan",
    "MathAtan2",
    "MathCeil",
    "MathCopysign",
    "MathCos",
    "MathDegrees",
    "MathExp",
    "MathFabs",
    "MathFactorial",
    "MathFloor",
    "MathFmod",
    "MathGcd",
    "MathHypot",
    "MathIsclose",
    "MathIsfinite",
    "MathIsinf",
    "MathIsnan",
    "MathIsqrt",
    "MathLog",
    "MathLog2",
    "MathLog10",
    "MathPow",
    "MathRadians",
    "MathSin",
    "MathSqrt",
    "MathTan",
    "MathTrunc",
]


# --- powers and roots -------------------------------------------------------

MathSqrt = ScalarQueryFactory("MathSqrt", math.sqrt)
MathPow = ScalarQueryFactory("MathPow", math.pow)
MathExp = ScalarQueryFactory("MathExp", math.exp)
MathIsqrt = ScalarQueryFactory("MathIsqrt", math.isqrt)
MathHypot = ScalarQueryFactory("MathHypot", math.hypot)

# --- logarithms -------------------------------------------------------------

MathLog = ScalarQueryFactory("MathLog", math.log)
MathLog2 = ScalarQueryFactory("MathLog2", math.log2)
MathLog10 = ScalarQueryFactory("MathLog10", math.log10)

# --- trigonometry -----------------------------------------------------------

MathSin = ScalarQueryFactory("MathSin", math.sin)
MathCos = ScalarQueryFactory("MathCos", math.cos)
MathTan = ScalarQueryFactory("MathTan", math.tan)
MathAsin = ScalarQueryFactory("MathAsin", math.asin)
MathAcos = ScalarQueryFactory("MathAcos", math.acos)
MathAtan = ScalarQueryFactory("MathAtan", math.atan)
MathAtan2 = ScalarQueryFactory("MathAtan2", math.atan2)
MathDegrees = ScalarQueryFactory("MathDegrees", math.degrees)
MathRadians = ScalarQueryFactory("MathRadians", math.radians)

# --- rounding and absolute --------------------------------------------------

MathFloor = ScalarQueryFactory("MathFloor", math.floor)
MathCeil = ScalarQueryFactory("MathCeil", math.ceil)
MathTrunc = ScalarQueryFactory("MathTrunc", math.trunc)
MathFabs = ScalarQueryFactory("MathFabs", math.fabs)
MathCopysign = ScalarQueryFactory("MathCopysign", math.copysign)
MathFmod = ScalarQueryFactory("MathFmod", math.fmod)

# --- integer functions ------------------------------------------------------

MathGcd = ScalarQueryFactory("MathGcd", math.gcd)
MathFactorial = ScalarQueryFactory("MathFactorial", math.factorial)

# --- classification ---------------------------------------------------------

MathIsclose = ScalarQueryFactory("MathIsclose", math.isclose)
MathIsnan = ScalarQueryFactory("MathIsnan", math.isnan)
MathIsinf = ScalarQueryFactory("MathIsinf", math.isinf)
MathIsfinite = ScalarQueryFactory("MathIsfinite", math.isfinite)
