"""cmath interactions - one ``ScalarQueryFactory`` binding per host call.

Two groups, both bound straight to a host callable:

- the ``complex`` value type: its constructor (``ComplexOf`` binds the
  ``complex`` builtin) and the ``conjugate`` method (binds the *unbound* method,
  a plain callable whose first argument is the receiver). Property reads
  (``.real`` / ``.imag``) reuse core ``GetAttrQuery``; arithmetic and equality
  reuse the core atoms - none of those are here.
- the ``cmath`` free functions (``sqrt``, ``exp``, ``phase``, ``polar`` ...),
  each bound straight to the ``cmath.*`` callable, exactly like ``nu.std.math``.

Constants (``pi``, ``e``, ``infj`` ...) are plain values, so they need no atom -
they ride on ``LiteralQuery`` in ``functions``.

Every binding here is pure (no clock, no randomness), so a future
constant-folding pass may fold any of them freely.
"""

from __future__ import annotations

import cmath
from builtins import complex as _complex

from nu.lang import ScalarQueryFactory


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

ComplexOf = ScalarQueryFactory("ComplexOf", _complex)
ComplexConjugate = ScalarQueryFactory("ComplexConjugate", _complex.conjugate)

# --- powers and roots -------------------------------------------------------

CmathSqrt = ScalarQueryFactory("CmathSqrt", cmath.sqrt)
CmathExp = ScalarQueryFactory("CmathExp", cmath.exp)

# --- logarithms -------------------------------------------------------------

CmathLog = ScalarQueryFactory("CmathLog", cmath.log)
CmathLog10 = ScalarQueryFactory("CmathLog10", cmath.log10)

# --- trigonometry -----------------------------------------------------------

CmathSin = ScalarQueryFactory("CmathSin", cmath.sin)
CmathCos = ScalarQueryFactory("CmathCos", cmath.cos)
CmathTan = ScalarQueryFactory("CmathTan", cmath.tan)
CmathAsin = ScalarQueryFactory("CmathAsin", cmath.asin)
CmathAcos = ScalarQueryFactory("CmathAcos", cmath.acos)
CmathAtan = ScalarQueryFactory("CmathAtan", cmath.atan)
CmathSinh = ScalarQueryFactory("CmathSinh", cmath.sinh)
CmathCosh = ScalarQueryFactory("CmathCosh", cmath.cosh)
CmathTanh = ScalarQueryFactory("CmathTanh", cmath.tanh)

# --- polar conversions ------------------------------------------------------

CmathPhase = ScalarQueryFactory("CmathPhase", cmath.phase)
CmathPolar = ScalarQueryFactory("CmathPolar", cmath.polar)
CmathRect = ScalarQueryFactory("CmathRect", cmath.rect)

# --- classification ---------------------------------------------------------

CmathIsnan = ScalarQueryFactory("CmathIsnan", cmath.isnan)
CmathIsinf = ScalarQueryFactory("CmathIsinf", cmath.isinf)
CmathIsfinite = ScalarQueryFactory("CmathIsfinite", cmath.isfinite)
CmathIsclose = ScalarQueryFactory("CmathIsclose", cmath.isclose)
