"""Basic bracket-tree Nu app: mem-navigator preset + a tiny compute.

The "hello world" of the bracket form. One ``nu.With(...)`` tree wraps a
``memory_navigator`` preset around a body that stores + reads a counter,
then ``nu.run(tree)`` drives the whole thing sync -- no hand-wired Context,
no event loop.

Run: python examples/brackets/basic.py
"""

from __future__ import annotations

import nu
from nu.domains.shape import Shape
from nu.virtuals import IntRef


class Counter(Shape):
    """One int slot, backed by whatever the outer bracket binds."""

    value = IntRef.slot()


# Init -> bump -> read. Transaction wraps the writes, Snapshot the read.
body = (
    nu.v.Transaction(Counter.value.store(0) >> Counter.value.store(Counter.value + 42))
    >> nu.v.Snapshot(nu.print(Counter.value))
)

# The whole app as one bracket tree: mem stack + body.
tree = nu.With(
    nu.v.presets.memory_navigator(),
    body=body,
)


if __name__ == "__main__":
    nu.run(tree)
