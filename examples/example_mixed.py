"""Mixed shapes example: multiple PV shapes in one flow."""

from __future__ import annotations

import everypv as pv
from everybase.abc.flows import Print, Seq
from everyshape import Shape


# --- Shapes ---


class Counters(Shape):
    """In-memory counters."""

    a = pv.IntRef.slot()
    b = pv.IntRef.slot()


class Results(Shape):
    """Persisted results."""

    total = pv.IntRef.slot()


# --- Tree ---


tree = Seq(
    Counters.a.set(10),
    Counters.b.set(20),
    Results.total.set(Counters.a.get() + Counters.b.get()),
    Print("Result", Results.total),
)


# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from everybase import Context
    from everypv.adapters.codecs import TextCodec as Codec
    from everypv.adapters.storages.textdb import TextStorage as Storage
    from everypv.views import DictView

    with Storage(".db-mixed", codec=Codec()) as storage:
        ctx = (
            Context()
            .with_handle(StorageProtocol, storage, shape=Counters)
            .with_handle(StorageProtocol, storage, shape=Results)
        )

        wrapped = pv.auto_atomic(tree, Counters, DictView)
        wrapped = pv.auto_atomic(wrapped, Results, DictView)
        await wrapped.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
