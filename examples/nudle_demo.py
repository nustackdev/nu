"""nudle demo - run a Nu and explore state via browser."""

import asyncio

from nudle import arun_ui

import nu
import nu_virtuals as nv
from nu.shapes import Shape


class Meta(Shape):
    label = nv.StrRef.slot()
    version = nv.IntRef.slot()


class Counter(Shape):
    value = nv.IntRef.slot()
    step = nv.IntRef.slot()
    tags = nv.ListRef.slot(str)
    meta = nv.ShapeRef.slot(Meta)


async def main() -> None:
    from nu_virtuals import auto_atomic
    from nu_virtuals.presets import rocksdb_storage_inmemory
    from virtuals import Navigator

    with rocksdb_storage_inmemory(".db") as storage:
        nav = Navigator(storage)
        ctx = nu.Context().bind(Navigator, nav)

        app = (
            nu.If(Counter.value.missing(), Counter.value.store(0))
            >> nu.If(Counter.step.missing(), Counter.step.store(1))
            >> Counter.meta.label.store("demo")
            >> Counter.meta.version.store(1)
            >> Counter.tags.store(["seed"])
            >> Counter.value.inc()
            >> Counter.value.inc(Counter.step)
            >> Counter.value.inc(Counter.step * 2)
            >> Counter.step.store(Counter.step + 1)
            >> Counter.value.store(Counter.value * 2)
            >> Counter.tags.store(["seed", "doubled"])
            >> Counter.meta.version.inc()
            >> nu.Print("value:", Counter.value, "step:", Counter.step)
        )

        await auto_atomic(app).execute(ctx)

        await arun_ui(Counter, nav.storage, port=8001)


if __name__ == "__main__":
    asyncio.run(main())
