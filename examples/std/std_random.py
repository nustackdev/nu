"""nu.std.random seed: a typed random surface built the v2 way.

Imported like the stdlib: ``from nu.std.random import randint, choice`` (or
``import nu.std.random as random``). ``random`` is a function module, so the
surface is free functions - no central class. Each wrapper builds an atom bound
to the matching ``random.*`` callable and returns the right Form (float, int,
list, or any element). Every draw is non-deterministic, so output varies run to
run. Each entry prints run result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.random import (
    choice,
    gauss,
    getrandbits,
    randint,
    random,
    sample,
    uniform,
)


ctx = Context()

# 1. A dice roll - an Int in 1..6 (RandomRandint atom).
e1 = randint(1, 6)
print(run(e1, ctx)[0], type(e1), e1)

# 2. Pick one element - an Any (RandomChoice atom).
e2 = choice(["red", "green", "blue"])
print(run(e2, ctx)[0], type(e2), e2)

# 3. A uniform real in [0, 1) - a Float.
e3 = uniform(0, 1)
print(run(e3, ctx)[0], type(e3), e3)

# 4. Two distinct picks without replacement - a List.
e4 = sample([1, 2, 3, 4, 5], 2)
print(run(e4, ctx)[0], type(e4), e4)

# 5. A standard-normal draw - a Float.
e5 = gauss(0, 1)
print(run(e5, ctx)[0], type(e5), e5)

# 6. Eight random bits as an int (0..255) - an Int.
e6 = getrandbits(8)
print(run(e6, ctx)[0], type(e6), e6)

# 7. The base draw - a Float in [0.0, 1.0).
e7 = random()
print(run(e7, ctx)[0], type(e7), e7)
