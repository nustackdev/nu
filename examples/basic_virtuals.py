"""Basic virtuals example - counter Shape with scoped ops.

Shows: Shape definition, refs, Transaction (write), Snapshot (read).
A counter Shape gets incremented inside a Transaction,
then read and printed inside a Snapshot.
"""

import asyncio

import nu
import nu_virtuals as nv


class Counter(nu.Shape):
    """A shape with a single integer counter."""

    value = nv.IntRef.slot()


# A simple Nu app
app = (
    # Write: initialize and increment counter 3 times
    nv.Transaction(
        nu.If(
            Counter.value.missing(),
            Counter.value.store(0),
        ),
        Counter.value.store(Counter.value + 1),
        Counter.value.store(Counter.value + 1),
        Counter.value.store(Counter.value + 1),
    )
    # Read: print current value
    >> nv.Snapshot(
        nu.Print("counter", Counter.value),
    )
    # Write: increment more
    >> nv.Transaction(
        Counter.value.store(Counter.value + 10),
    )
    # Read: print again
    >> nv.Snapshot(
        nu.Print("counter", Counter.value),
    )
)


async def main() -> None:
    """Run the app."""
    from nu_virtuals.presets import rocksdb_storage_inmemory
    from virtuals import Navigator

    with rocksdb_storage_inmemory(".dbtest") as storage:
        nav = Navigator(storage)
        ctx = nu.Context().bind(Navigator, nav)

        await app.aexecute(ctx)


asyncio.run(main())
