"""Module-level functions and constants for ``nu.std.math``.

``math`` has no central class, so this is the whole surface: typed wrappers that
mirror ``math.sqrt`` / ``math.floor`` / ``math.gcd`` 1-1, plus the module
constants (``pi``, ``e``, ``tau``, ``inf``, ``nan``). Each wrapper builds its
interaction atom (lazily imported, like ``nu.std.uuid``) and returns the Form
that matches the host return type:

- most functions -> ``Float``
- ``floor`` / ``ceil`` / ``trunc`` / ``gcd`` / ``factorial`` / ``isqrt`` -> ``Int``
- ``isnan`` / ``isinf`` / ``isfinite`` / ``isclose`` -> ``Bool``

Constants are plain values, so they ride on ``Literal`` instead of an atom.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from nu import Bool, Float, Int
from nu.core import Literal


if TYPE_CHECKING:
    from nu.lang import FloatArg, IntArg


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


# --- constants --------------------------------------------------------------

pi = Float(Literal(math.pi))
e = Float(Literal(math.e))
tau = Float(Literal(math.tau))
inf = Float(Literal(math.inf))
nan = Float(Literal(math.nan))


# --- powers and roots -------------------------------------------------------


def sqrt(x: FloatArg) -> Float:
    """The square root of ``x``: mirrors ``math.sqrt()``."""
    from .interactions import MathSqrt

    return Float(MathSqrt(x))


def pow(base: FloatArg, exp: FloatArg) -> Float:
    """``base`` raised to ``exp``: mirrors ``math.pow()``."""
    from .interactions import MathPow

    return Float(MathPow(base, exp))


def exp(x: FloatArg) -> Float:
    """``e`` raised to ``x``: mirrors ``math.exp()``."""
    from .interactions import MathExp

    return Float(MathExp(x))


def isqrt(x: IntArg) -> Int:
    """The integer square root of ``x``: mirrors ``math.isqrt()``."""
    from .interactions import MathIsqrt

    return Int(MathIsqrt(x))


def hypot(x: FloatArg, y: FloatArg) -> Float:
    """The Euclidean norm ``sqrt(x*x + y*y)``: mirrors ``math.hypot()``."""
    from .interactions import MathHypot

    return Float(MathHypot(x, y))


# --- logarithms -------------------------------------------------------------


def log(x: FloatArg, base: FloatArg | None = None) -> Float:
    """The logarithm of ``x`` (natural, or to ``base``): mirrors ``math.log()``."""
    from .interactions import MathLog

    if base is not None:
        return Float(MathLog(x, base))
    return Float(MathLog(x))


def log2(x: FloatArg) -> Float:
    """The base-2 logarithm of ``x``: mirrors ``math.log2()``."""
    from .interactions import MathLog2

    return Float(MathLog2(x))


def log10(x: FloatArg) -> Float:
    """The base-10 logarithm of ``x``: mirrors ``math.log10()``."""
    from .interactions import MathLog10

    return Float(MathLog10(x))


# --- trigonometry -----------------------------------------------------------


def sin(x: FloatArg) -> Float:
    """The sine of ``x`` radians: mirrors ``math.sin()``."""
    from .interactions import MathSin

    return Float(MathSin(x))


def cos(x: FloatArg) -> Float:
    """The cosine of ``x`` radians: mirrors ``math.cos()``."""
    from .interactions import MathCos

    return Float(MathCos(x))


def tan(x: FloatArg) -> Float:
    """The tangent of ``x`` radians: mirrors ``math.tan()``."""
    from .interactions import MathTan

    return Float(MathTan(x))


def asin(x: FloatArg) -> Float:
    """The arc sine of ``x``, in radians: mirrors ``math.asin()``."""
    from .interactions import MathAsin

    return Float(MathAsin(x))


def acos(x: FloatArg) -> Float:
    """The arc cosine of ``x``, in radians: mirrors ``math.acos()``."""
    from .interactions import MathAcos

    return Float(MathAcos(x))


def atan(x: FloatArg) -> Float:
    """The arc tangent of ``x``, in radians: mirrors ``math.atan()``."""
    from .interactions import MathAtan

    return Float(MathAtan(x))


def atan2(y: FloatArg, x: FloatArg) -> Float:
    """The arc tangent of ``y/x``, respecting quadrant: mirrors ``math.atan2()``."""
    from .interactions import MathAtan2

    return Float(MathAtan2(y, x))


def degrees(x: FloatArg) -> Float:
    """Radians ``x`` converted to degrees: mirrors ``math.degrees()``."""
    from .interactions import MathDegrees

    return Float(MathDegrees(x))


def radians(x: FloatArg) -> Float:
    """Degrees ``x`` converted to radians: mirrors ``math.radians()``."""
    from .interactions import MathRadians

    return Float(MathRadians(x))


# --- rounding and absolute --------------------------------------------------


def floor(x: FloatArg) -> Int:
    """The floor of ``x`` as an int: mirrors ``math.floor()``."""
    from .interactions import MathFloor

    return Int(MathFloor(x))


def ceil(x: FloatArg) -> Int:
    """The ceiling of ``x`` as an int: mirrors ``math.ceil()``."""
    from .interactions import MathCeil

    return Int(MathCeil(x))


def trunc(x: FloatArg) -> Int:
    """``x`` truncated toward zero as an int: mirrors ``math.trunc()``."""
    from .interactions import MathTrunc

    return Int(MathTrunc(x))


def fabs(x: FloatArg) -> Float:
    """The absolute value of ``x`` as a float: mirrors ``math.fabs()``."""
    from .interactions import MathFabs

    return Float(MathFabs(x))


def copysign(x: FloatArg, y: FloatArg) -> Float:
    """``x`` with the sign of ``y``: mirrors ``math.copysign()``."""
    from .interactions import MathCopysign

    return Float(MathCopysign(x, y))


def fmod(x: FloatArg, y: FloatArg) -> Float:
    """The C-library ``fmod`` of ``x`` and ``y``: mirrors ``math.fmod()``."""
    from .interactions import MathFmod

    return Float(MathFmod(x, y))


# --- integer functions ------------------------------------------------------


def gcd(a: IntArg, b: IntArg) -> Int:
    """The greatest common divisor of ``a`` and ``b``: mirrors ``math.gcd()``."""
    from .interactions import MathGcd

    return Int(MathGcd(a, b))


def factorial(x: IntArg) -> Int:
    """``x`` factorial: mirrors ``math.factorial()``."""
    from .interactions import MathFactorial

    return Int(MathFactorial(x))


# --- classification ---------------------------------------------------------


def isclose(a: FloatArg, b: FloatArg) -> Bool:
    """Whether ``a`` and ``b`` are close: mirrors ``math.isclose()``."""
    from .interactions import MathIsclose

    return Bool(MathIsclose(a, b))


def isnan(x: FloatArg) -> Bool:
    """Whether ``x`` is NaN: mirrors ``math.isnan()``."""
    from .interactions import MathIsnan

    return Bool(MathIsnan(x))


def isinf(x: FloatArg) -> Bool:
    """Whether ``x`` is positive or negative infinity: mirrors ``math.isinf()``."""
    from .interactions import MathIsinf

    return Bool(MathIsinf(x))


def isfinite(x: FloatArg) -> Bool:
    """Whether ``x`` is finite: mirrors ``math.isfinite()``."""
    from .interactions import MathIsfinite

    return Bool(MathIsfinite(x))
