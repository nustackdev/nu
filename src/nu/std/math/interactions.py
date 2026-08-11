"""math interactions - one ``host`` binding per host call.

``math`` is a function module: no central class, just free functions over
floats and ints. Core can't compute ``sqrt``/``sin``/etc., so each one is a new
atom bound straight to the ``math.*`` callable. Constants (``pi``, ``e``, ...)
are plain values, so they need no atom - they ride on ``Literal`` in
``functions``.

Every binding here is pure (no clock, no randomness), so a future
constant-folding pass may fold any of them freely.
"""

from __future__ import annotations

import math

from nu.factory import host


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

MathSqrt = host(math.sqrt, name="MathSqrt")
MathPow = host(math.pow, name="MathPow")
MathExp = host(math.exp, name="MathExp")
MathIsqrt = host(math.isqrt, name="MathIsqrt")
MathHypot = host(math.hypot, name="MathHypot")

# --- logarithms -------------------------------------------------------------

MathLog = host(math.log, name="MathLog")
MathLog2 = host(math.log2, name="MathLog2")
MathLog10 = host(math.log10, name="MathLog10")

# --- trigonometry -----------------------------------------------------------

MathSin = host(math.sin, name="MathSin")
MathCos = host(math.cos, name="MathCos")
MathTan = host(math.tan, name="MathTan")
MathAsin = host(math.asin, name="MathAsin")
MathAcos = host(math.acos, name="MathAcos")
MathAtan = host(math.atan, name="MathAtan")
MathAtan2 = host(math.atan2, name="MathAtan2")
MathDegrees = host(math.degrees, name="MathDegrees")
MathRadians = host(math.radians, name="MathRadians")

# --- rounding and absolute --------------------------------------------------

MathFloor = host(math.floor, name="MathFloor")
MathCeil = host(math.ceil, name="MathCeil")
MathTrunc = host(math.trunc, name="MathTrunc")
MathFabs = host(math.fabs, name="MathFabs")
MathCopysign = host(math.copysign, name="MathCopysign")
MathFmod = host(math.fmod, name="MathFmod")

# --- integer functions ------------------------------------------------------

MathGcd = host(math.gcd, name="MathGcd")
MathFactorial = host(math.factorial, name="MathFactorial")

# --- classification ---------------------------------------------------------

MathIsclose = host(math.isclose, name="MathIsclose")
MathIsnan = host(math.isnan, name="MathIsnan")
MathIsinf = host(math.isinf, name="MathIsinf")
MathIsfinite = host(math.isfinite, name="MathIsfinite")
