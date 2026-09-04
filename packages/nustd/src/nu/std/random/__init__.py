"""Nu surface for Python's ``random`` module.

``random`` is a function module - module-level functions over a global RNG, no
central class - so the Nu surface mirrors that: free functions (``random``,
``randint``, ``choice``, ``sample``, ...). Two layers behind it: ``functions``
(the typed wrappers) and ``interactions`` (the atoms each wrapper builds). Import
it the way you would the stdlib::

    from nu.std.random import randint, choice
    import nu.std.random as random     # then random.randint(1, 6)

Every function reads the global RNG. The effectful / stateful pieces (``seed``,
``shuffle``, ``getstate`` / ``setstate``) are deferred until the effect model
lands.
"""

from __future__ import annotations

from nu.std.random.functions import (
    choice,
    choices,
    expovariate,
    gauss,
    getrandbits,
    normalvariate,
    randint,
    random,
    randrange,
    sample,
    triangular,
    uniform,
)


__all__ = [
    "choice",
    "choices",
    "expovariate",
    "gauss",
    "getrandbits",
    "normalvariate",
    "randint",
    "random",
    "randrange",
    "sample",
    "triangular",
    "uniform",
]
