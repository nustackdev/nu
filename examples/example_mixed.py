"""Mixed substrate example: dict (memory) + PV (disk) in one flow."""

from __future__ import annotations

import every_dict as mem
import every_flow as f
import every_pv as pv
from everyshape import Shape


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

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage
    from every_pv.views import DictView
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
