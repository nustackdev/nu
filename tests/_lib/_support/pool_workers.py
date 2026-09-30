"""Helpers for the ``nustd.mp_pool`` tests that have to survive a ``spawn``.

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


__all__ = ["RESIDENT", "Marker"]


class Marker:
    """A trivial fabric a worker can be brought up holding, to prove ``init`` ran.

    Bound on the child's Context by an ``init`` bracket; a teleported
    ``FabricRef(Marker)`` read then sees it.
    """

    def __init__(self, label: str = "unset") -> None:
        self.label = label

    def setup(self, ctx: object) -> None:
        """Nothing to build; the instance is the whole fabric."""


# A body that never terminates: the thing Dispatch exists for. It holds no
# state across calls, so a test watches it through the pool (running, cancel,
# kill), never by reading back what it wrote.
RESIDENT = nu.ForeverDo(nu.Delay(0.005))
