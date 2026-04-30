"""nu-inspect demo -- render a Shape and a Nu app, then run the app.

Shows ``render_shape`` on a nested Shape + ``render_nu`` on a multi-step app.
"""

import nu
import nu_mem as nm
from nu_inspect import render_nu, render_shape


class Meta(nu.Shape):
    label = nm.StrRef.slot()
    version = nm.IntRef.slot()


class Counter(nu.Shape):
    value = nm.IntRef.slot()
    step = nm.IntRef.slot()
    tags = nm.ListRef.slot(str)
    meta = nm.ShapeRef.slot(Meta)


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

data = {}

print("=== Shape (before) ===")
print(render_shape(Counter, data))

print("\n=== App ===")
print(render_nu(app))

print("\n=== Running ===")
app.execute(nu.Context().bind(dict, data))

print("\n=== Shape (after) ===")
print(render_shape(Counter, data))
