"""nu.std.decimal seed: ``decimal.Decimal`` as a Form, the v2 way.

Imported like the stdlib: ``from nu.std.decimal import Decimal``. Constructors
and method calls are factory atoms; arithmetic and comparison reuse the core
atoms (Python does the real Decimal op on the resolved values, so precision is
exact). Each entry prints run result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.decimal import Decimal


ctx = Context()

# 1. Build a decimal from a string, exactly (DecimalOf coerces via str).
e1 = Decimal.of("3.14")
print(run(e1, ctx)[0], type(e1), e1)

# 2. Exact addition: 0.1 + 0.2 == 0.3, not 0.30000000000000004 (core Add).
e2 = Decimal.of("0.1") + Decimal.of("0.2")
print(run(e2, ctx)[0], type(e2), e2)

# 3. Quantize to two places (factory atom over Decimal.quantize).
e3 = Decimal.of("3.14159").quantize(Decimal.of("0.01"))
print(run(e3, ctx)[0], type(e3), e3)

# 4. Square root (factory atom over Decimal.sqrt).
e4 = Decimal.of("2").sqrt()
print(run(e4, ctx)[0], type(e4), e4)

# 5. Comparison via the < operator (core Lt).
e5 = Decimal.of("1.5") < Decimal.of("2.5")
print(run(e5, ctx)[0], type(e5), e5)

# 6. A predicate (factory atom over Decimal.is_finite).
e6 = Decimal.of("10").is_finite()
print(run(e6, ctx)[0], type(e6), e6)

# 7. compare: -1 / 0 / 1 for less / equal / greater (factory atom).
e7 = Decimal.of("1").compare(Decimal.of("2"))
print(run(e7, ctx)[0], type(e7), e7)
