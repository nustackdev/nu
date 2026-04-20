"""nu-inspect demo -- render a Shape and a Nu app, then run the app.

Shows ``render_shape`` on a nested Shape + ``render_nu`` on a multi-step app.
"""

import asyncio

import nu
import nu_dict as nd
from nu.shapes import Shape
from nu_inspect import render_nu, render_shape


class Meta(Shape):
    label = nd.StrRef.slot()
    version = nd.IntRef.slot()


class Counter(Shape):
    value = nd.IntRef.slot()
    step = nd.IntRef.slot()
    tags = nd.ListRef.slot(str)
    meta = nd.ShapeRef.slot(Meta)


async def main() -> None:
    data: dict = {}
    ctx = nu.Context().bind(dict, data, Counter)

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

    print("=== Shape (before) ===")
    print(render_shape(Counter, data))

    print("\n=== App ===")
    print(render_nu(app))

    print("\n=== Running ===")
    await app.execute(ctx)

    print("\n=== Shape (after) ===")
    print(render_shape(Counter, data))


if __name__ == "__main__":
    asyncio.run(main())
