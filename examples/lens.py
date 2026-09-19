"""Lens: walk a live kv store in the browser, one column per step.

Arrows move, right opens, left goes back, and a click does the same thing as
the keys. Four things are worth watching, and the second one is the point of
the whole surface.

- **The columns are read, not sent.** Nothing about this store is in the
  browser bundle. Each move ships one cursor up, and the server walks the Shape
  from that cursor, reads exactly the slots that column needs, and ships the
  whole cascade back. Drill into ``machines`` and you are looking at what
  storage answered a millisecond ago.
- **The second lens cannot leave red.** It is anchored at
  ``Cluster.machines["red"]`` and pointed at ``Machine``. The cursor it sends
  is relative to that Shape, and where the Shape lives never leaves the
  program, so there is no crumb for ``machines`` and no way back up to
  ``blue``. Try: the breadcrumb's "root" is red, and that is as far out as it
  goes. Same store as the lens above it, a different amount of it.
- **A declared container shows what a program actually wrote.** ``scratch`` is
  declared as a mapping and nothing else. Open it and the keys are whatever got
  put there, of whatever types, none of them named by any Shape. The shape
  supplies the protocol, kv supplies the contents.
- **An unwritten slot says so.** The mac has no ``gpu``, and the row reads
  ``empty`` rather than an empty string, because that is a different fact. Red
  has a ``last_error`` that was written as null, and that row reads ``none``.
  Three kinds of nothing, three different words.

Also worth a look: ``notes`` is a long string, and a column holding one value
drops the row grammar and becomes a reader pane. And the two lenses are wired
two different ways -- the top one with ``browse``, the anchored one out of the
primitives ``browse`` is built from -- which is the same surface either way.

Run: uv run python examples/lens.py   ->   http://localhost:8091
"""

import nu
import nustd


# ---- the store --------------------------------------------------------------


class Disk(nu.Shape):
    mount = nustd.kv.StrRef.slot()
    size_gb = nustd.kv.IntRef.slot()
    ssd = nustd.kv.BoolRef.slot()


class Machine(nu.Shape):
    name = nustd.kv.StrRef.slot()
    role = nustd.kv.StrRef.slot()
    cores = nustd.kv.IntRef.slot()
    ram_gb = nustd.kv.IntRef.slot()
    gpu = nustd.kv.StrRef.slot()
    tags = nustd.kv.ListRef.slot(str)
    disks = nustd.kv.ShapesListRef.slot(Disk)
    counters = nustd.kv.DictRef.slot(int)
    # Declared as a mapping and nothing more. Whatever a program drops in here
    # shows up in the column, keys and types included.
    scratch = nustd.kv.DictRef.slot(object)


class Cluster(nu.Shape):
    name = nustd.kv.StrRef.slot()
    notes = nustd.kv.StrRef.slot()
    machines = nustd.kv.ShapesDictRef.slot(Machine)


NOTES = (
    "Three boxes on one switch. red and blue share the grid over NFS, so a file "
    "written on either is the same file; the mac keeps its own checkouts and "
    "converges through git. The GPUs live on red and blue, which is why the mac "
    "is the only one here with nothing in its gpu slot. Everything in this store "
    "was written by the seed below, and the lens above is reading it back out of "
    "storage one column at a time."
)


def _machine(key, name, role, cores, ram, gpu, tags, disks, counters, scratch):
    """One machine, written under ``key``."""
    at = Cluster.machines[key]
    written = (
        at.name.set(nu.Str(name))
        | at.role.set(nu.Str(role))
        | at.cores.set(nu.Int(cores))
        | at.ram_gb.set(nu.Int(ram))
        | at.tags.init(nu.List.create())
        | at.disks.init(nu.List.create())
        | at.counters.init(nu.Dict.create())
        | at.scratch.init(nu.Dict.create())
    )
    if gpu:
        written = written | at.gpu.set(nu.Str(gpu))
    filled = at.tags.set(tags) >> at.disks.set(disks)
    for k, v in counters.items():
        filled = filled >> at.counters.set_item(nu.Str(k), nu.Int(v))
    for k, v in scratch.items():
        filled = filled >> at.scratch.set_item(nu.Str(k), nu.Literal(v))
    return written >> filled


seed = (
    (Cluster.name.set(nu.Str("arkkln")) | Cluster.notes.set(nu.Str(NOTES)))
    >> _machine(
        "red",
        name="red",
        role="workstation",
        cores=24,
        ram=128,
        gpu="RTX 4090",
        tags=["gpu", "nfs-host", "primary"],
        disks=[
            {"mount": "/", "size_gb": 2000, "ssd": True},
            {"mount": "/grid", "size_gb": 8000, "ssd": True},
        ],
        counters={"jobs_run": 1841, "restarts": 3, "gpu_oom": 0},
        scratch={
            "last_sync": "2026-09-18T22:41:09",
            "queue_depth": 7,
            "degraded": False,
            "last_error": None,
        },
    )
    >> _machine(
        "blue",
        name="blue",
        role="workstation",
        cores=16,
        ram=64,
        gpu="RTX 3090",
        tags=["gpu", "nfs-client"],
        disks=[{"mount": "/", "size_gb": 1000, "ssd": True}],
        counters={"jobs_run": 402, "restarts": 11, "gpu_oom": 2},
        scratch={"last_sync": "2026-09-18T22:41:12", "queue_depth": 0},
    )
    >> _machine(
        "mac",
        name="mac",
        role="portable",
        cores=12,
        ram=36,
        gpu="",
        tags=["laptop", "hub"],
        disks=[{"mount": "/", "size_gb": 1000, "ssd": True}],
        counters={"jobs_run": 96, "restarts": 0},
        scratch={"tunnels": 2},
    )
)


# ---- the page ---------------------------------------------------------------


class Whole(nustd.ui.Card):
    lens = nustd.ui.lens.LensRef.slot(height=460)


class Anchored(nustd.ui.Card):
    lens = nustd.ui.lens.LensRef.slot(height=360)


class Home(nustd.ui.Page):
    heading = nustd.ui.HeadingRef.slot(label="What is in the store")
    whole = Whole.slot(title="the cluster, from the top")
    anchored = Anchored.slot(title="red, and only ever red")


class App(nustd.ui.Index):
    title = nustd.ui.TitleRef.slot(default="Lens")
    home = Home.slot("/")


# ---- the wiring -------------------------------------------------------------
#
# Two lenses, two ways of getting one. The top lens is `browse`: hand it a
# shape and a prefix and it hands back a working surface. The anchored one is
# the same thing spelled out underneath, which is what `browse` is doing for
# you and all it is doing.


def by_hand(lens, shape, prefix, key):
    """Paint the root column, then repaint the cascade on every move.

    The cursor is the browser's, so the arm is a pure "recompute the columns
    for whatever cursor you were handed" loop and remembers nothing between
    frames.

    The two reads of ``key`` are built separately on purpose: a Nu node is a
    value, and one object sitting in two tree positions is one compiled node
    that the two of them would then share at runtime.

    The ``Snapshot`` is not optional. The walk builds a term at run time, and a
    term built at run time is invisible to the pass that would otherwise place
    the storage boundary for you. It is also the one thing in here that knows
    what a store is, which is why it is the line `browse` exists to write.
    """
    boot = nustd.kv.Snapshot(
        lens.set_columns(
            nu.List.of(),
            nustd.ui.lens.columns(shape, nu.List.of(), prefix=prefix),
        )
    )
    on_nav = nu.ReactForever(
        lens.on_nav(),
        nustd.kv.Snapshot(
            lens.set_columns(
                nu.ListAttrRef(key),
                nustd.ui.lens.columns(shape, nu.ListAttrRef(key), prefix=prefix),
            )
        ),
        changed_key=key,
    )
    return boot >> on_nav


ui = (
    App.title.set("Lens")
    # Seed once. A second tab finds the cluster already there and writes nothing.
    >> nustd.kv.Transaction(nu.IfDo(Cluster.name.missing(), seed))
    # ParallelAsync and not `|`: each arm builds its term at run time, and the
    # smart Parallel refuses to pick a mode for a branch it cannot see into.
    >> nu.ParallelAsync(
        nustd.ui.lens.browse(App.home.whole.lens, Cluster),
        by_hand(App.home.anchored.lens, Machine, Cluster.machines["red"], "red_nav"),
    )
)

# In memory: the store is a fixture, and a restart is meant to hand back the
# same three machines rather than whatever the last run left behind.
app = nu.With(nustd.kv.memory_navigator(), body=nustd.ui.serve(App, ui, port=8091))


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
