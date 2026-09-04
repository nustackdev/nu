"""Module-level functions and constants for ``nu.std.cmath``.

``cmath`` is a function module - free functions over complex numbers plus a few
constants - so this is the function half of the surface: typed wrappers that
mirror ``cmath.sqrt`` / ``cmath.phase`` / ``cmath.polar`` 1-1, plus the module
constants. Each wrapper builds its interaction atom (lazily imported, like
``nu.std.math``) and returns the Form that matches the host return type:

- most functions -> ``complex`` (the Form for the builtin)
- ``phase`` -> ``Float``
- ``polar`` -> ``Tuple`` (the ``(r, phi)`` pair)
- ``isnan`` / ``isinf`` / ``isfinite`` / ``isclose`` -> ``Bool``
- ``rect(r, phi)`` -> ``complex``

Constants are plain values, so they ride on ``Literal`` instead of an atom.
``pi`` / ``e`` / ``tau`` / ``inf`` / ``nan`` are floats; ``infj`` / ``nanj`` are
complex, so they are wrapped in the ``complex`` Form.
"""

from __future__ import annotations

import cmath
from typing import TYPE_CHECKING

from nu.forms import Bool, Float, Tuple
from nu.lang import Literal

from .forms import complex


if TYPE_CHECKING:
    from nu.lang import FloatArg

    from .forms import ComplexArg


__all__ = [
    "acos",
    "asin",
    "atan",
    "cos",
    "cosh",
    "e",
    "exp",
    "inf",
    "infj",
    "isclose",
    "isfinite",
    "isinf",
    "isnan",
    "log",
    "log10",
    "nan",
    "nanj",
    "phase",
    "pi",
    "polar",
    "rect",
    "sin",
    "sinh",
    "sqrt",
    "tan",
    "tanh",
    "tau",
]


# --- constants --------------------------------------------------------------

pi = Float(Literal(cmath.pi))
e = Float(Literal(cmath.e))
tau = Float(Literal(cmath.tau))
inf = Float(Literal(cmath.inf))
nan = Float(Literal(cmath.nan))
infj = complex(Literal(cmath.infj))
nanj = complex(Literal(cmath.nanj))


# --- powers and roots -------------------------------------------------------


def sqrt(x: ComplexArg) -> complex:
    """The square root of ``x``: mirrors ``cmath.sqrt()``."""
    from .interactions import CmathSqrt

    return complex(CmathSqrt(x))


def exp(x: ComplexArg) -> complex:
    """``e`` raised to ``x``: mirrors ``cmath.exp()``."""
    from .interactions import CmathExp

    return complex(CmathExp(x))


# --- logarithms -------------------------------------------------------------


def log(x: ComplexArg, base: ComplexArg | None = None) -> complex:
    """The logarithm of ``x`` (natural, or to ``base``): mirrors ``cmath.log()``."""
    from .interactions import CmathLog

    if base is not None:
        return complex(CmathLog(x, base))
    return complex(CmathLog(x))


def log10(x: ComplexArg) -> complex:
    """The base-10 logarithm of ``x``: mirrors ``cmath.log10()``."""
    from .interactions import CmathLog10

    return complex(CmathLog10(x))


# --- trigonometry -----------------------------------------------------------


def sin(x: ComplexArg) -> complex:
    """The sine of ``x``: mirrors ``cmath.sin()``."""
    from .interactions import CmathSin

    return complex(CmathSin(x))


def cos(x: ComplexArg) -> complex:
    """The cosine of ``x``: mirrors ``cmath.cos()``."""
    from .interactions import CmathCos

    return complex(CmathCos(x))


def tan(x: ComplexArg) -> complex:
    """The tangent of ``x``: mirrors ``cmath.tan()``."""
    from .interactions import CmathTan

    return complex(CmathTan(x))


def asin(x: ComplexArg) -> complex:
    """The arc sine of ``x``: mirrors ``cmath.asin()``."""
    from .interactions import CmathAsin

    return complex(CmathAsin(x))


def acos(x: ComplexArg) -> complex:
    """The arc cosine of ``x``: mirrors ``cmath.acos()``."""
    from .interactions import CmathAcos

    return complex(CmathAcos(x))


def atan(x: ComplexArg) -> complex:
    """The arc tangent of ``x``: mirrors ``cmath.atan()``."""
    from .interactions import CmathAtan

    return complex(CmathAtan(x))


def sinh(x: ComplexArg) -> complex:
    """The hyperbolic sine of ``x``: mirrors ``cmath.sinh()``."""
    from .interactions import CmathSinh

    return complex(CmathSinh(x))


def cosh(x: ComplexArg) -> complex:
    """The hyperbolic cosine of ``x``: mirrors ``cmath.cosh()``."""
    from .interactions import CmathCosh

    return complex(CmathCosh(x))


def tanh(x: ComplexArg) -> complex:
    """The hyperbolic tangent of ``x``: mirrors ``cmath.tanh()``."""
    from .interactions import CmathTanh

    return complex(CmathTanh(x))


# --- polar conversions ------------------------------------------------------


def phase(x: ComplexArg) -> Float:
    """The phase angle of ``x``, in radians: mirrors ``cmath.phase()``."""
    from .interactions import CmathPhase

    return Float(CmathPhase(x))


def polar(x: ComplexArg) -> Tuple:
    """``x`` as the polar pair ``(r, phi)``: mirrors ``cmath.polar()``."""
    from .interactions import CmathPolar

    return Tuple(CmathPolar(x))


def rect(r: FloatArg, phi: FloatArg) -> complex:
    """The complex number with modulus ``r`` and phase ``phi``: mirrors ``cmath.rect()``."""
    from .interactions import CmathRect

    return complex(CmathRect(r, phi))


# --- classification ---------------------------------------------------------


def isnan(x: ComplexArg) -> Bool:
    """Whether ``x`` has a NaN component: mirrors ``cmath.isnan()``."""
    from .interactions import CmathIsnan

    return Bool(CmathIsnan(x))


def isinf(x: ComplexArg) -> Bool:
    """Whether ``x`` has an infinite component: mirrors ``cmath.isinf()``."""
    from .interactions import CmathIsinf

    return Bool(CmathIsinf(x))


def isfinite(x: ComplexArg) -> Bool:
    """Whether both components of ``x`` are finite: mirrors ``cmath.isfinite()``."""
    from .interactions import CmathIsfinite

    return Bool(CmathIsfinite(x))


def isclose(a: ComplexArg, b: ComplexArg) -> Bool:
    """Whether ``a`` and ``b`` are close: mirrors ``cmath.isclose()``."""
    from .interactions import CmathIsclose

    return Bool(CmathIsclose(a, b))
