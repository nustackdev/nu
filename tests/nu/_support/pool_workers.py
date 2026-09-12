"""Helpers for the ``nu.mp_pool`` tests that have to survive a ``spawn``.

Under the default ``spawn`` start method a worker's ``init`` bracket is pickled
into the child, and a class is pickled *by reference*. Anything a test wants a
worker to come up holding therefore has to live in an importable module, not in
the test file (which pytest imports by path under ``--import-mode=importlib``).

Nu terms are different: they pickle by value, so a resident body or a teleported
tree can be built inline in a test. The trees here are shared only because more
than one test wants them.
"""

from __future__ import annotations

import nu


__all__ = ["RESIDENT_TICKER", "SEED_TICK", "Marker", "read_tick"]


class Marker:
    """A trivial fabric a worker can be brought up holding, to prove ``init`` ran.

    Bound on the child's Context by an ``init`` bracket; a teleported
    ``FabricRef(Marker)`` read then sees it.
    """

    def __init__(self, label: str = "unset") -> None:
        self.label = label

    def setup(self, ctx: object) -> None:
        """Nothing to build; the instance is the whole fabric."""


# Seed the counter the resident body increments. A bare AttrRef read of an
# unset name is EMPTY, and EMPTY + 1 is INVALID, so the counter has to exist
# before the loop starts.
SEED_TICK = nu.SetCmd(nu.AttrRef("tick"), 0)

# A body that never terminates: the thing Dispatch exists for. It mutates the
# worker's own Context, so the parent can watch it move with a Teleport.
RESIDENT_TICKER = nu.ForeverDo(
    nu.DelayedDo(
        0.005,
        nu.SetCmd(nu.AttrRef("tick"), nu.Add(nu.AttrRef("tick"), 1)),
    )
)

# The read of that counter, to be teleported.
read_tick = nu.AttrRef("tick")
