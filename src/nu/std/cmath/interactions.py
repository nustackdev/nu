"""cmath interactions - one ``host`` binding per host call.

Two groups, both bound straight to a host callable:

- the ``complex`` value type: its constructor (``ComplexOf`` binds the
  ``complex`` builtin) and the ``conjugate`` method (binds the *unbound* method,
  a plain callable whose first argument is the receiver). Property reads
  (``.real`` / ``.imag``) reuse core ``GetAttr``; arithmetic and equality
  reuse the core atoms - none of those are here.
- the ``cmath`` free functions (``sqrt``, ``exp``, ``phase``, ``polar`` ...),
  each bound straight to the ``cmath.*`` callable, exactly like ``nu.std.math``.

Constants (``pi``, ``e``, ``infj`` ...) are plain values, so they need no atom -
they ride on ``Literal`` in ``functions``.

Every binding here is pure (no clock, no randomness), so a future
constant-folding pass may fold any of them freely.
"""

from __future__ import annotations

import cmath
from builtins import complex as _complex

from nu.factory import host


__all__ = [
    "CmathAcos",
    "CmathAsin",
    "CmathAtan",
    "CmathCos",
    "CmathCosh",
    "CmathExp",
    "CmathIsclose",
    "CmathIsfinite",
    "CmathIsinf",
    "CmathIsnan",
    "CmathLog",
    "CmathLog10",
    "CmathPhase",
    "CmathPolar",
    "CmathRect",
    "CmathSin",
    "CmathSinh",
    "CmathSqrt",
    "CmathTan",
    "CmathTanh",
    "ComplexConjugate",
    "ComplexOf",
]


# --- the complex value type -------------------------------------------------

ComplexOf = host(_complex, name="ComplexOf")
ComplexConjugate = host(_complex.conjugate, name="ComplexConjugate")

# --- powers and roots -------------------------------------------------------

CmathSqrt = host(cmath.sqrt, name="CmathSqrt")
CmathExp = host(cmath.exp, name="CmathExp")

# --- logarithms -------------------------------------------------------------

CmathLog = host(cmath.log, name="CmathLog")
CmathLog10 = host(cmath.log10, name="CmathLog10")

# --- trigonometry -----------------------------------------------------------

CmathSin = host(cmath.sin, name="CmathSin")
CmathCos = host(cmath.cos, name="CmathCos")
CmathTan = host(cmath.tan, name="CmathTan")
CmathAsin = host(cmath.asin, name="CmathAsin")
CmathAcos = host(cmath.acos, name="CmathAcos")
CmathAtan = host(cmath.atan, name="CmathAtan")
CmathSinh = host(cmath.sinh, name="CmathSinh")
CmathCosh = host(cmath.cosh, name="CmathCosh")
CmathTanh = host(cmath.tanh, name="CmathTanh")

# --- polar conversions ------------------------------------------------------

CmathPhase = host(cmath.phase, name="CmathPhase")
CmathPolar = host(cmath.polar, name="CmathPolar")
CmathRect = host(cmath.rect, name="CmathRect")

# --- classification ---------------------------------------------------------

CmathIsnan = host(cmath.isnan, name="CmathIsnan")
CmathIsinf = host(cmath.isinf, name="CmathIsinf")
CmathIsfinite = host(cmath.isfinite, name="CmathIsfinite")
CmathIsclose = host(cmath.isclose, name="CmathIsclose")
