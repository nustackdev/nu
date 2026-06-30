"""Minimal Shape sketches. One pattern per section. Each runs standalone.

Shapes = typed access to nested data. nu_mem is the dict-backed substrate:
the root is a plain Python `dict`, bound into a Context. Shape slots become
typed Refs you read/write through Nu ops.
"""

import nu
import nu_mem as nm


# --- util ---
def exec(app: nu.Nu):
    data: dict = {}
    ctx = nu.Context().bind(dict, data)
    print("return val:", app.collect(ctx))


# --- define some shapes ---
class Counter(nu.Shape):
    value = nm.IntRef.slot()


class User(nu.Shape):
    name = nm.StrRef.slot()
    age = nm.IntRef.slot()
    tags = nm.ListRef.slot(str)


class Score(nu.Shape):
    total = nm.IntRef.slot()
    hits = nm.IntRef.slot()


# --- bind a fresh dict as the substrate and run one write ---
exec(Counter.value.store(7) >> Counter.value)


# --- inc compiles to store(self + step); chain writes with >> ---
exec(Counter.value.store(0) >> Counter.value.inc() >> Counter.value.inc() >> Counter.value.inc(10))


# --- conditional init: only write if missing ---
exec(nu.If(Counter.value.missing(), Counter.value.store(0)) >> Counter.value.inc())


# --- a richer shape: multiple typed slots + a nested list ---
exec(
    User.name.store("mir") >> User.age.store(0) >> User.age.inc(30) >> User.tags.store(["ai", "nu"])
)


# --- compose a full app; `ctx` carries the substrate, ops do the rest ---
exec(
    nu.If(Score.total.missing(), Score.total.store(0))
    >> nu.If(Score.hits.missing(), Score.hits.store(0))
    >> Score.total.inc(42)
    >> Score.hits.inc()
    >> nu.Print("score:", Score.total, "hits:", Score.hits)
)
