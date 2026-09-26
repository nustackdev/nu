"""Shapes and trees for the ``nustd.valkey`` integration test.

Two ``mp_pool`` workers each bind a ``sqlite_navigator_redis`` stack on one
file. Worker B runs a resident reaction to ``Store.value``; worker A writes
it. The trees are teleported or dispatched to spawned workers, and the Shape
classes they name are pickled by reference, so they live here rather than in
the test file.
"""

from __future__ import annotations

import nu
import nustd


__all__ = ["B_BODY", "B_INIT", "READ_LAST", "READ_WAKES", "Seen", "Store", "a_burst", "a_set"]


class Store(nu.Shape):
    """What worker A writes."""

    value = nustd.kv.IntRef.slot()


class Seen(nu.Shape):
    """What worker B records each time it wakes."""

    wakes = nustd.kv.IntRef.slot()
    last = nustd.kv.IntRef.slot()


# B: on every change of Store.value, count the wake and keep the value seen.
B_BODY = nustd.kv.auto_flow_atomic(
    nu.ReactForever(
        Store.value.on_change(),
        Seen.wakes.inc() >> Seen.last.set(Store.value),
    ),
)
B_INIT = nustd.kv.auto_flow_atomic(Seen.wakes.set(0) >> Seen.last.set(-1))
READ_WAKES = nustd.kv.Snapshot(Seen.wakes)
READ_LAST = nustd.kv.Snapshot(Seen.last)


def a_set(v: int) -> nu.Nu:
    """One write of ``v`` from worker A."""
    return nustd.kv.Transaction(Store.value.set(v))


def a_burst(start: int, n: int) -> nu.Nu:
    """``n`` back-to-back writes from worker A, ending at ``start + n - 1``."""
    return nu.ForRangeDo(
        start,
        start + n,
        nustd.kv.Transaction(Store.value.set(nu.AttrRef("index"))),
    )
