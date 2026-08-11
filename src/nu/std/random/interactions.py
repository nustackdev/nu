"""random interactions - one ``host`` binding per host call.

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

from nu.factory import host


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

RandomRandom = host(random.random, name="RandomRandom", deterministic=False)
RandomUniform = host(random.uniform, name="RandomUniform", deterministic=False)
RandomRandint = host(random.randint, name="RandomRandint", deterministic=False)
RandomRandrange = host(random.randrange, name="RandomRandrange", deterministic=False)
RandomGetrandbits = host(random.getrandbits, name="RandomGetrandbits", deterministic=False)

# --- sequence draws ---------------------------------------------------------

RandomChoice = host(random.choice, name="RandomChoice", deterministic=False)
# ``random.choices`` takes ``k`` keyword-only; wrap so the atom can pass it
# positionally (factory atoms type-check as their base ScalarQuery init).
RandomChoices = host(
    lambda population, k: random.choices(population, k=k),  # noqa: S311 -- general RNG, not crypto
    name="RandomChoices",
    deterministic=False,
)
RandomSample = host(random.sample, name="RandomSample", deterministic=False)

# --- continuous distributions -----------------------------------------------

RandomGauss = host(random.gauss, name="RandomGauss", deterministic=False)
RandomNormalvariate = host(random.normalvariate, name="RandomNormalvariate", deterministic=False)
RandomExpovariate = host(random.expovariate, name="RandomExpovariate", deterministic=False)
RandomTriangular = host(random.triangular, name="RandomTriangular", deterministic=False)
