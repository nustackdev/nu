"""Basic virtuals example - counter Shape with scoped ops.

Shows: Shape definition, refs, Transaction (write), Snapshot (read).
A counter Shape gets incremented inside a Transaction,
then read and printed inside a Snapshot.
"""

import asyncio

from virtuals import Navigator

import nu
import nu_virtuals as nuv
from nu.shapes import Shape
from nu_virtuals.presets import rocksdb_storage_inmemory


class Counter(Shape):
    """A shape with a single integer counter."""

    value = nuv.IntRef.slot()


async def main():
    with rocksdb_storage_inmemory(".dbtest") as storage:
        nav = Navigator(storage)
        ctx = nu.Context().bind(Navigator, nav)

        tree = nu.Seq(
            # Write: initialize and increment counter 3 times
            nuv.Transaction(
                nu.If(
                    Counter.value.missing(),
                    Counter.value.store(0),
                ),
                Counter.value.store(Counter.value + 1),
                Counter.value.store(Counter.value + 1),
                Counter.value.store(Counter.value + 1),
            ),
            # Read: print current value
            nuv.Snapshot(
                nu.Print("counter", Counter.value),
            ),
            # Write: increment more
            nuv.Transaction(
                Counter.value.store(Counter.value + 10),
            ),
            # Read: print again
            nuv.Snapshot(
                nu.Print("counter", Counter.value),
            ),
        )

        await tree.execute(ctx)


asyncio.run(main())
