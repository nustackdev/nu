"""nu.std.math seed: a typed math surface built the v2 way.

Imported like the stdlib: ``from nu.std.math import sqrt, pi`` (or
``import nu.std.math as math``). ``math`` is a function module, so the surface is
free functions and constants - no central class. Each wrapper builds an atom
bound to the matching ``math.*`` callable and returns the right Form (float, int,
or bool). Each entry prints run result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.math import floor, gcd, hypot, isnan, pi, pow, sqrt


ctx = Context()

# 1. Square root - a Float (MathSqrt atom).
e1 = sqrt(2)
print(run(e1, ctx)[0], type(e1), e1)

# 2. Floor - returns an int, so a Float in maps to an Int out.
e2 = floor(3.7)
print(run(e2, ctx)[0], type(e2), e2)

# 3. Greatest common divisor - two ints in, an Int out.
e3 = gcd(12, 8)
print(run(e3, ctx)[0], type(e3), e3)

# 4. Power - mirrors math.pow (always a float).
e4 = pow(2, 10)
print(run(e4, ctx)[0], type(e4), e4)

# 5. Euclidean norm of a 3-4-5 triangle - a Float.
e5 = hypot(3, 4)
print(run(e5, ctx)[0], type(e5), e5)

# 6. NaN check - a Bool.
e6 = isnan(0.0)
print(run(e6, ctx)[0], type(e6), e6)

# 7. A constant - pi rides on Literal, no atom needed.
e7 = pi
print(run(e7, ctx)[0], type(e7), e7)
