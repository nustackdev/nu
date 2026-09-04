"""Nu surface for Python's ``itertools`` module.

``itertools`` is a function module - free functions that build and combine
iterators, no central class - so the Nu surface mirrors that: free functions
over Nu streams. Two layers behind it: ``functions`` (the wrappers) and
``interactions`` (the hand-written ``StreamQuery`` atoms each wrapper builds,
hot path, e2e, no factory).

A gap-fill: members already in Nu core (``map`` / ``filter`` / ``zip`` /
``sorted`` / ``enumerate`` / ``reversed`` / sums and folds) are not repeated
here. Import it the way you would the stdlib::

    from nu.std.itertools import chain, islice, count
    import nu.std.itertools as itertools     # then itertools.product(a, b)
"""

from __future__ import annotations

from nu.std.itertools.functions import (
    accumulate,
    batched,
    chain,
    chain_from_iterable,
    combinations,
    combinations_with_replacement,
    compress,
    count,
    cycle,
    dropwhile,
    filterfalse,
    groupby,
    islice,
    pairwise,
    permutations,
    product,
    repeat,
    starmap,
    takewhile,
    tee,
    zip_longest,
)


__all__ = [
    "accumulate",
    "batched",
    "chain",
    "chain_from_iterable",
    "combinations",
    "combinations_with_replacement",
    "compress",
    "count",
    "cycle",
    "dropwhile",
    "filterfalse",
    "groupby",
    "islice",
    "pairwise",
    "permutations",
    "product",
    "repeat",
    "starmap",
    "takewhile",
    "tee",
    "zip_longest",
]
