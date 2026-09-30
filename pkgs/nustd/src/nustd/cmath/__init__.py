"""Nu surface for Python's ``complex`` builtin and its ``cmath`` companion.

A hybrid surface: ``complex`` is a builtin with no module of its own, and
``cmath`` is its set of companion functions, so the two co-locate here. The
surface mirrors both 1-1:

- the ``complex`` value type is a Form (``complex.of(real, imag)``, ``.real`` /
  ``.imag``, ``conjugate()``, arithmetic, ``eq`` / ``ne``).
- the ``cmath`` free functions (``sqrt``, ``exp``, ``phase``, ``polar``, ...)
  and constants (``pi``, ``e``, ``tau``, ``inf``, ``nan``, ``infj``, ``nanj``).

Three layers behind it: ``forms`` (the ``complex`` type), ``functions`` (the
``cmath`` wrappers and constants), and ``interactions`` (the atoms each builds).
Import it the way you would the stdlib::

    from nustd.cmath import complex, sqrt, phase, pi
    import nustd.cmath as cmath    # then cmath.sqrt(...), cmath.phase(...)

The leaves that hold these values in a Shape slot sit one submodule per
fabric: ``nustd.cmath.mem`` for ``nu.mem``, loaded with this package, and
``nustd.cmath.kv`` for ``nustd.kv``, imported by its own path.
"""

from __future__ import annotations

from nustd.cmath import mem
from nustd.cmath.forms import complex
from nustd.cmath.functions import (
    acos,
    asin,
    atan,
    cos,
    cosh,
    e,
    exp,
    inf,
    infj,
    isclose,
    isfinite,
    isinf,
    isnan,
    log,
    log10,
    nan,
    nanj,
    phase,
    pi,
    polar,
    rect,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
    tau,
)


__all__ = [
    "acos",
    "asin",
    "atan",
    "complex",
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
    "mem",
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
