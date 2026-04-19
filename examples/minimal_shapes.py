"""Minimal Shape sketches. One pattern per section. Each runs standalone.

Shapes = typed access to nested data. nu_dict is the dict-backed substrate:
the root is a plain Python `dict`, bound into a Context. Shape slots become
typed Refs you read/write through Nu ops.
"""

import asyncio

import nu
import nu_dict as nd
from nu.shapes import Shape


# --- define a shape: slots are typed refs ---
class Counter(Shape):
    value = nd.IntRef.slot()


# --- bind a fresh dict as the substrate and run one write ---
data: dict = {}
ctx = nu.Context().bind(dict, data, Counter)
asyncio.run(Counter.value.store(7).execute(ctx))
print(data)  # {'value': 7}


# --- read back through the ref; first() drains the open generator ---
print(asyncio.run(Counter.value.first(ctx)))  # 7


# --- inc compiles to store(self + step); chain writes with >> ---
app = Counter.value.inc() >> Counter.value.inc() >> Counter.value.inc(10)
asyncio.run(app.execute(ctx))
print(data["value"])  # 19


# --- conditional init: only write if missing ---
data2: dict = {}
ctx2 = nu.Context().bind(dict, data2, Counter)
init = nu.If(Counter.value.missing(), Counter.value.store(0))
asyncio.run((init >> Counter.value.inc()).execute(ctx2))
print(data2["value"])  # 1


# --- a richer shape: multiple typed slots + a nested list ---
class User(Shape):
    name = nd.StrRef.slot()
    age = nd.IntRef.slot()
    tags = nd.ListRef.slot(str)


udata: dict = {}
uctx = nu.Context().bind(dict, udata, User)
setup = (
    User.name.store("mir")
    >> User.age.store(0)
    >> User.age.inc(30)
    >> User.tags.store(["ai", "nu"])
)
asyncio.run(setup.execute(uctx))
print(udata)  # {'name': 'mir', 'age': 30, 'tags': ['ai', 'nu']}


# --- expressions over refs: arithmetic flows through store ---
asyncio.run(User.age.store(User.age * 2).execute(uctx))
print(udata["age"])  # 60


# --- compose a full app; `ctx` carries the substrate, ops do the rest ---
class Score(Shape):
    total = nd.IntRef.slot()
    hits = nd.IntRef.slot()


sdata: dict = {}
sctx = nu.Context().bind(dict, sdata, Score)
app = (
    nu.If(Score.total.missing(), Score.total.store(0))
    >> nu.If(Score.hits.missing(), Score.hits.store(0))
    >> Score.total.inc(42)
    >> Score.hits.inc()
    >> nu.Print("score:", Score.total, "hits:", Score.hits)
)
asyncio.run(app.execute(sctx))
