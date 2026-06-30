"""Module-level functions and constants for ``nu.std.math``.

``math`` has no central class, so this is the whole surface: typed wrappers that
mirror ``math.sqrt`` / ``math.floor`` / ``math.gcd`` 1-1, plus the module
constants (``pi``, ``e``, ``tau``, ``inf``, ``nan``). Each wrapper builds its
interaction atom (lazily imported, like ``nu.std.uuid``) and returns the Form
that matches the host return type:

- most functions -> ``FloatForm``
- ``floor`` / ``ceil`` / ``trunc`` / ``gcd`` / ``factorial`` / ``isqrt`` -> ``IntForm``
- ``isnan`` / ``isinf`` / ``isfinite`` / ``isclose`` -> ``BoolForm``

Constants are plain values, so they ride on ``LiteralQuery`` instead of an atom.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from nu import BoolForm, FloatForm, IntForm
from nu.core import LiteralQuery


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

pi = FloatForm(LiteralQuery(math.pi))
e = FloatForm(LiteralQuery(math.e))
tau = FloatForm(LiteralQuery(math.tau))
inf = FloatForm(LiteralQuery(math.inf))
nan = FloatForm(LiteralQuery(math.nan))


# --- powers and roots -------------------------------------------------------


def sqrt(x: FloatArg) -> FloatForm:
    """The square root of ``x``: mirrors ``math.sqrt()``."""
    from .interactions import MathSqrt

    return FloatForm(MathSqrt(x))


def pow(base: FloatArg, exp: FloatArg) -> FloatForm:
    """``base`` raised to ``exp``: mirrors ``math.pow()``."""
    from .interactions import MathPow

    return FloatForm(MathPow(base, exp))


def exp(x: FloatArg) -> FloatForm:
    """``e`` raised to ``x``: mirrors ``math.exp()``."""
    from .interactions import MathExp

    return FloatForm(MathExp(x))


def isqrt(x: IntArg) -> IntForm:
    """The integer square root of ``x``: mirrors ``math.isqrt()``."""
    from .interactions import MathIsqrt

    return IntForm(MathIsqrt(x))


def hypot(x: FloatArg, y: FloatArg) -> FloatForm:
    """The Euclidean norm ``sqrt(x*x + y*y)``: mirrors ``math.hypot()``."""
    from .interactions import MathHypot

    return FloatForm(MathHypot(x, y))


# --- logarithms -------------------------------------------------------------


def log(x: FloatArg, base: FloatArg | None = None) -> FloatForm:
    """The logarithm of ``x`` (natural, or to ``base``): mirrors ``math.log()``."""
    from .interactions import MathLog

    if base is not None:
        return FloatForm(MathLog(x, base))
    return FloatForm(MathLog(x))


def log2(x: FloatArg) -> FloatForm:
    """The base-2 logarithm of ``x``: mirrors ``math.log2()``."""
    from .interactions import MathLog2

    return FloatForm(MathLog2(x))


def log10(x: FloatArg) -> FloatForm:
    """The base-10 logarithm of ``x``: mirrors ``math.log10()``."""
    from .interactions import MathLog10

    return FloatForm(MathLog10(x))


# --- trigonometry -----------------------------------------------------------


def sin(x: FloatArg) -> FloatForm:
    """The sine of ``x`` radians: mirrors ``math.sin()``."""
    from .interactions import MathSin

    return FloatForm(MathSin(x))


def cos(x: FloatArg) -> FloatForm:
    """The cosine of ``x`` radians: mirrors ``math.cos()``."""
    from .interactions import MathCos

    return FloatForm(MathCos(x))


def tan(x: FloatArg) -> FloatForm:
    """The tangent of ``x`` radians: mirrors ``math.tan()``."""
    from .interactions import MathTan

    return FloatForm(MathTan(x))


def asin(x: FloatArg) -> FloatForm:
    """The arc sine of ``x``, in radians: mirrors ``math.asin()``."""
    from .interactions import MathAsin

    return FloatForm(MathAsin(x))


def acos(x: FloatArg) -> FloatForm:
    """The arc cosine of ``x``, in radians: mirrors ``math.acos()``."""
    from .interactions import MathAcos

    return FloatForm(MathAcos(x))


def atan(x: FloatArg) -> FloatForm:
    """The arc tangent of ``x``, in radians: mirrors ``math.atan()``."""
    from .interactions import MathAtan

    return FloatForm(MathAtan(x))


def atan2(y: FloatArg, x: FloatArg) -> FloatForm:
    """The arc tangent of ``y/x``, respecting quadrant: mirrors ``math.atan2()``."""
    from .interactions import MathAtan2

    return FloatForm(MathAtan2(y, x))


def degrees(x: FloatArg) -> FloatForm:
    """Radians ``x`` converted to degrees: mirrors ``math.degrees()``."""
    from .interactions import MathDegrees

    return FloatForm(MathDegrees(x))


def radians(x: FloatArg) -> FloatForm:
    """Degrees ``x`` converted to radians: mirrors ``math.radians()``."""
    from .interactions import MathRadians

    return FloatForm(MathRadians(x))


# --- rounding and absolute --------------------------------------------------


def floor(x: FloatArg) -> IntForm:
    """The floor of ``x`` as an int: mirrors ``math.floor()``."""
    from .interactions import MathFloor

    return IntForm(MathFloor(x))


def ceil(x: FloatArg) -> IntForm:
    """The ceiling of ``x`` as an int: mirrors ``math.ceil()``."""
    from .interactions import MathCeil

    return IntForm(MathCeil(x))


def trunc(x: FloatArg) -> IntForm:
    """``x`` truncated toward zero as an int: mirrors ``math.trunc()``."""
    from .interactions import MathTrunc

    return IntForm(MathTrunc(x))


def fabs(x: FloatArg) -> FloatForm:
    """The absolute value of ``x`` as a float: mirrors ``math.fabs()``."""
    from .interactions import MathFabs

    return FloatForm(MathFabs(x))


def copysign(x: FloatArg, y: FloatArg) -> FloatForm:
    """``x`` with the sign of ``y``: mirrors ``math.copysign()``."""
    from .interactions import MathCopysign

    return FloatForm(MathCopysign(x, y))


def fmod(x: FloatArg, y: FloatArg) -> FloatForm:
    """The C-library ``fmod`` of ``x`` and ``y``: mirrors ``math.fmod()``."""
    from .interactions import MathFmod

    return FloatForm(MathFmod(x, y))


# --- integer functions ------------------------------------------------------


def gcd(a: IntArg, b: IntArg) -> IntForm:
    """The greatest common divisor of ``a`` and ``b``: mirrors ``math.gcd()``."""
    from .interactions import MathGcd

    return IntForm(MathGcd(a, b))


def factorial(x: IntArg) -> IntForm:
    """``x`` factorial: mirrors ``math.factorial()``."""
    from .interactions import MathFactorial

    return IntForm(MathFactorial(x))


# --- classification ---------------------------------------------------------


def isclose(a: FloatArg, b: FloatArg) -> BoolForm:
    """Whether ``a`` and ``b`` are close: mirrors ``math.isclose()``."""
    from .interactions import MathIsclose

    return BoolForm(MathIsclose(a, b))


def isnan(x: FloatArg) -> BoolForm:
    """Whether ``x`` is NaN: mirrors ``math.isnan()``."""
    from .interactions import MathIsnan

    return BoolForm(MathIsnan(x))


def isinf(x: FloatArg) -> BoolForm:
    """Whether ``x`` is positive or negative infinity: mirrors ``math.isinf()``."""
    from .interactions import MathIsinf

    return BoolForm(MathIsinf(x))


def isfinite(x: FloatArg) -> BoolForm:
    """Whether ``x`` is finite: mirrors ``math.isfinite()``."""
    from .interactions import MathIsfinite

    return BoolForm(MathIsfinite(x))
