"""nu.std.cmath seed: the ``complex`` type plus the ``cmath`` functions, v2 way.

Imported like the stdlib: ``from nu.std.cmath import complex, sqrt, pi`` (or
``import nu.std.cmath as cmath``). A hybrid surface - ``complex`` is a value-type
Form (``.of(...)``, ``.real`` / ``.imag``, ``conjugate()``, arithmetic, abs),
``cmath`` is the companion free functions and constants. Each entry prints run
result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.cmath import complex, phase, pi, sqrt


ctx = Context()

# 1. Build a complex number, take its magnitude - abs of 3+4j is 5.0 (Float).
e1 = abs(complex.of(3, 4))
print(run(e1, ctx)[0], type(e1), e1)

# 2. The conjugate - flips the imaginary sign (a complex Form).
e2 = complex.of(3, 4).conjugate()
print(run(e2, ctx)[0], type(e2), e2)

# 3. The real part - a property read (core GetAttr).
e3 = complex.of(3, 4).real()
print(run(e3, ctx)[0], type(e3), e3)

# 4. The imaginary part - a property read (core GetAttr).
e4 = complex.of(3, 4).imag()
print(run(e4, ctx)[0], type(e4), e4)

# 5. cmath.sqrt of -1 - the complex square root j (CmathSqrt atom).
e5 = sqrt(complex.of(-1, 0))
print(run(e5, ctx)[0], type(e5), e5)

# 6. The phase angle of 1j - pi/2, a Float (CmathPhase atom).
e6 = phase(complex.of(0, 1))
print(run(e6, ctx)[0], type(e6), e6)

# 7. A constant - pi rides on Literal, no atom needed.
e7 = pi
print(run(e7, ctx)[0], type(e7), e7)
