"""nu.std.fractions seed: ``fractions.Fraction`` as a Form, the v2 way.

Imported like the stdlib: ``from nu.std.fractions import Fraction``. Property
reads reuse core GetAttr; method calls bind the unbound Fraction methods;
arithmetic and comparison reuse the core atoms (Python does the real rational op
on the resolved values). Each entry prints run result, term type, and the
expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.fractions import Fraction


ctx = Context()

# 1. Build a fraction (FractionOf).
e1 = Fraction.of(1, 3)
print(run(e1, ctx)[0], type(e1), e1)

# 2. Exact rational arithmetic: 1/3 + 1/6 == 1/2 (core Add).
e2 = (Fraction.of(1, 3) + Fraction.of(1, 6)).eq(Fraction.of(1, 2))
print(run(e2, ctx)[0], type(e2), e2)

# 3. Read the numerator (core GetAttr), in lowest terms.
e3 = Fraction.of(2, 4).numerator()
print(run(e3, ctx)[0], type(e3), e3)

# 4. Read the denominator (core GetAttr).
e4 = Fraction.of(2, 4).denominator()
print(run(e4, ctx)[0], type(e4), e4)

# 5. limit_denominator (method atom over the unbound Fraction method).
e5 = Fraction.from_float(3.141592653589793).limit_denominator(100)
print(run(e5, ctx)[0], type(e5), e5)

# 6. Comparison via the < operator (core Lt).
e6 = Fraction.of(1, 3) < Fraction.of(1, 2)
print(run(e6, ctx)[0], type(e6), e6)

# 7. from_float: the exact fraction equal to a float.
e7 = Fraction.from_float(0.5)
print(run(e7, ctx)[0], type(e7), e7)
