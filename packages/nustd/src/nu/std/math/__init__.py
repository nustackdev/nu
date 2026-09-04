"""Nu surface for Python's ``math`` module.

``math`` is a function module - module-level functions and constants, no central
class - so the Nu surface mirrors that: free functions (``sqrt``, ``sin``,
``gcd``, ...) and constants (``pi``, ``e``, ``tau``, ``inf``, ``nan``). Two
layers behind it: ``functions`` (the wrappers and constants) and
``interactions`` (the atoms each wrapper builds). Import it the way you would the
stdlib::

    from nu.std.math import sqrt, pi
    import nu.std.math as math     # then math.sqrt(2), math.floor(3.7)
"""

from __future__ import annotations

from nu.std.math.functions import (
    acos,
    asin,
    atan,
    atan2,
    ceil,
    copysign,
    cos,
    degrees,
    e,
    exp,
    fabs,
    factorial,
    floor,
    fmod,
    gcd,
    hypot,
    inf,
    isclose,
    isfinite,
    isinf,
    isnan,
    isqrt,
    log,
    log2,
    log10,
    nan,
    pi,
    pow,
    radians,
    sin,
    sqrt,
    tan,
    tau,
    trunc,
)


__all__ = [
    "acos",
    "asin",
    "atan",
    "atan2",
    "ceil",
    "copysign",
    "cos",
    "degrees",
    "e",
    "exp",
    "fabs",
    "factorial",
    "floor",
    "fmod",
    "gcd",
    "hypot",
    "inf",
    "isclose",
    "isfinite",
    "isinf",
    "isnan",
    "isqrt",
    "log",
    "log2",
    "log10",
    "nan",
    "pi",
    "pow",
    "radians",
    "sin",
    "sqrt",
    "tan",
    "tau",
    "trunc",
]
