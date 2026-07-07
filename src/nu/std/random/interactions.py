"""random interactions - one ``ScalarQueryFactory`` binding per host call.

``random`` is a function module: no central class, just free functions over
the global RNG. Core can't draw random numbers, so each one is a new atom bound
straight to the ``random.*`` callable.

Every binding here is NON-DETERMINISTIC - each reads the process-global RNG, the
same way ``uuid.uuid4`` / ``datetime.now`` do. So none of these atoms may be
constant-folded: two runs of the same tree must be free to differ. Each declares
``deterministic=False`` (the algebra attribute), which a folding/caching pass
reads to keep them un-folded (fold gate = pure AND deterministic).
"""

from __future__ import annotations

import random

from nu.factory import ScalarQueryFactory


__all__ = [
    "RandomChoice",
    "RandomChoices",
    "RandomExpovariate",
    "RandomGauss",
    "RandomGetrandbits",
    "RandomNormalvariate",
    "RandomRandint",
    "RandomRandom",
    "RandomRandrange",
    "RandomSample",
    "RandomTriangular",
    "RandomUniform",
]


# --- uniform reals and ints -------------------------------------------------

RandomRandom = ScalarQueryFactory("RandomRandom", random.random, deterministic=False)
RandomUniform = ScalarQueryFactory("RandomUniform", random.uniform, deterministic=False)
RandomRandint = ScalarQueryFactory("RandomRandint", random.randint, deterministic=False)
RandomRandrange = ScalarQueryFactory("RandomRandrange", random.randrange, deterministic=False)
RandomGetrandbits = ScalarQueryFactory("RandomGetrandbits", random.getrandbits, deterministic=False)

# --- sequence draws ---------------------------------------------------------

RandomChoice = ScalarQueryFactory("RandomChoice", random.choice, deterministic=False)
# ``random.choices`` takes ``k`` keyword-only; wrap so the atom can pass it
# positionally (factory atoms type-check as their base ScalarQuery init).
RandomChoices = ScalarQueryFactory(
    "RandomChoices",
    lambda population, k: random.choices(population, k=k),  # noqa: S311 -- general RNG, not crypto
    deterministic=False,
)
RandomSample = ScalarQueryFactory("RandomSample", random.sample, deterministic=False)

# --- continuous distributions -----------------------------------------------

RandomGauss = ScalarQueryFactory("RandomGauss", random.gauss, deterministic=False)
RandomNormalvariate = ScalarQueryFactory(
    "RandomNormalvariate", random.normalvariate, deterministic=False
)
RandomExpovariate = ScalarQueryFactory("RandomExpovariate", random.expovariate, deterministic=False)
RandomTriangular = ScalarQueryFactory("RandomTriangular", random.triangular, deterministic=False)
