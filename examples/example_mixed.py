"""Mixed substrate example: dict (memory) + PV (disk) in one flow."""

from __future__ import annotations

import eb_dict as mem
import eb_flow as f
import eb_pv as pv
from eb_shape import Shape


# --- Shapes ---


class Counters(Shape):
    """In-memory counters (dict substrate)."""

    a = mem.IntRef.slot()
    b = mem.IntRef.slot()


class Results(Shape):
    """Persisted results (PV substrate)."""

    total = pv.IntRef.slot()


# --- Tree ---


tree = f.Print(
    "Result",
    Results.total.set(Counters.a.set(10) + Counters.b.set(20)),
)


# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from eb_pv.adapters.codecs import TextCodec as Codec
    from eb_pv.adapters.storages.textdb import TextStorage as Storage
    from eb_pv.views import DictView
    from everybase import Context

    data: dict = {}
    with Storage(".db-mixed", codec=Codec()) as storage:
        ctx = (
            Context()
            .with_handle(dict, data, shape=Counters)
            .with_handle(StorageProtocol, storage, shape=Results)
        )

        wrapped = pv.auto_atomic(tree, Results, DictView)
        await wrapped.execute(ctx)

        print(f"\ndict backing: {data}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
