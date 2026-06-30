"""random interactions - one ``ScalarQueryFactory`` binding per host call.

``random`` is a function module: no central class, just free functions over
the global RNG. Core can't draw random numbers, so each one is a new atom bound
straight to the ``random.*`` callable.

Every binding here is NON-DETERMINISTIC - each reads the process-global RNG, the
same way ``uuid.uuid4`` / ``datetime.now`` do. So none of these atoms may be
constant-folded: two runs of the same tree must be free to differ. This is an
open item until the model grows a purity tag; there is no purity mechanism yet.
"""

from __future__ import annotations

import random

from nu.lang import ScalarQueryFactory


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

RandomRandom = ScalarQueryFactory("RandomRandom", random.random)
RandomUniform = ScalarQueryFactory("RandomUniform", random.uniform)
RandomRandint = ScalarQueryFactory("RandomRandint", random.randint)
RandomRandrange = ScalarQueryFactory("RandomRandrange", random.randrange)
RandomGetrandbits = ScalarQueryFactory("RandomGetrandbits", random.getrandbits)

# --- sequence draws ---------------------------------------------------------

RandomChoice = ScalarQueryFactory("RandomChoice", random.choice)
# ``random.choices`` takes ``k`` keyword-only; wrap so the atom can pass it
# positionally (factory atoms type-check as their base ScalarQuery init).
RandomChoices = ScalarQueryFactory(
    "RandomChoices",
    lambda population, k: random.choices(population, k=k),  # noqa: S311 -- general RNG, not crypto
)
RandomSample = ScalarQueryFactory("RandomSample", random.sample)

# --- continuous distributions -----------------------------------------------

RandomGauss = ScalarQueryFactory("RandomGauss", random.gauss)
RandomNormalvariate = ScalarQueryFactory("RandomNormalvariate", random.normalvariate)
RandomExpovariate = ScalarQueryFactory("RandomExpovariate", random.expovariate)
RandomTriangular = ScalarQueryFactory("RandomTriangular", random.triangular)
