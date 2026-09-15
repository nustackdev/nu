"""random interactions - one ``host`` binding per host call.

``random`` is a function module: no central class, just free functions over
the global RNG. Core can't draw random numbers, so each one is a new atom bound
straight to the ``random.*`` callable.

Every binding here reads the process-global RNG, the same way ``uuid.uuid4`` /
``datetime.now`` do. Two runs of the same tree are free to differ.
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

RandomRandom = host(random.random, name="RandomRandom")
RandomUniform = host(random.uniform, name="RandomUniform")
RandomRandint = host(random.randint, name="RandomRandint")
RandomRandrange = host(random.randrange, name="RandomRandrange")
RandomGetrandbits = host(random.getrandbits, name="RandomGetrandbits")

# --- sequence draws ---------------------------------------------------------

RandomChoice = host(random.choice, name="RandomChoice")
# ``random.choices`` takes ``k`` keyword-only; wrap so the atom can pass it
# positionally (factory atoms type-check as their base ScalarQuery init).
RandomChoices = host(
    lambda population, k: random.choices(population, k=k),  # noqa: S311 -- general RNG, not crypto
    name="RandomChoices",
)
RandomSample = host(random.sample, name="RandomSample")

# --- continuous distributions -----------------------------------------------

RandomGauss = host(random.gauss, name="RandomGauss")
RandomNormalvariate = host(random.normalvariate, name="RandomNormalvariate")
RandomExpovariate = host(random.expovariate, name="RandomExpovariate")
RandomTriangular = host(random.triangular, name="RandomTriangular")
