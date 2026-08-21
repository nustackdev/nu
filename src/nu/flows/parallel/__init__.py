"""Parallel-family flows: Parallel, Race, AnyN, plus Parallel forced-mode variants.

The ``|`` / ``&`` operator sugar gives ``Parallel`` and ``Race``; ``AnyN`` is
constructor-only. Only ``Parallel`` has forced-mode variants:

- ``Parallel`` / ``ParallelThreaded`` / ``ParallelAsync``
- ``Race`` (async-only, smart placement, no per-child override)
- ``AnyN`` (async-only, smart placement, no per-child override)

Parallel placement precedence per child: the parent's ``_FORCE_MODE`` (from
``ParallelThreaded`` / ``ParallelAsync``) wins first; then a per-child override
passed as ``(child, "threaded"|"async")``; otherwise the smart choice off
``Attr.ON_LOOP``. Example::

    Parallel(io_child, (cpu_child, "threaded"))   # smart + one override
    ParallelAsync(io_a, io_b)                     # every child on the loop

``Gather`` is a yield-collecting alias for ``Parallel``; scheduling
primitives live in ``_scheduling`` as free functions on ``rt``.
"""

from __future__ import annotations

from .anyn import AnyN
from .parallel import Gather, Parallel, ParallelAsync, ParallelThreaded
from .race import Race


__all__ = [
    "AnyN",
    "Gather",
    "Parallel",
    "ParallelAsync",
    "ParallelThreaded",
    "Race",
]
