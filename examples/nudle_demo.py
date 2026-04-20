"""nudle demo - run a Nu and explore state via browser."""

import asyncio

import nu
import nu_virtuals as nv
import nudle
import virtuals as v


class Meta(nu.Shape):
    label = nv.StrRef.slot()
    version = nv.IntRef.slot()


class Counter(nu.Shape):
    value = nv.IntRef.slot()
    step = nv.IntRef.slot()
    tags = nv.ListRef.slot(str)
    meta = nv.ShapeRef.slot(Meta)


async def main() -> None:
    from nu_virtuals.presets import rocksdb_storage_inmemory

    with rocksdb_storage_inmemory(".db") as storage:
        nav = v.Navigator(storage)
        ctx = nu.Context().bind(v.Navigator, nav)

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

        await nv.auto_atomic(app).execute(ctx)

        await nudle.arun_ui(Counter, nav.storage, port=8001)


if __name__ == "__main__":
    asyncio.run(main())
