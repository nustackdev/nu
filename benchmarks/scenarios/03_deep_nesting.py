"""Scenario: Deep Nesting -- 8-level shape hierarchy, leaf field access.

Stress test for ref chain resolution: each field op traverses 8 levels
of parent refs. This is where inline_refs should show the biggest gain
since it eliminates O(depth) recursive resolve per operation.

Structure: L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7.field
Each level has a single child shape keyed by "k0".."k6".
L7 has 4 scalar fields (a, b, c, d).

Modes:
  pure dict        -- imperative Python baseline
  PV Atomic        -- single Atomic wrapping entire Seq
  PV Atomic+inline -- PV with inline_refs deformation
  everydict        -- plain dict substrate
  everydict+inline -- everydict with inline_refs deformation

Benchmarks:
  write  -- set all 4 leaf fields (N times)
  read   -- get all 4 leaf fields (N times)
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import time


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)
from virtuals.tkv.tkv.storage import StorageProtocol

import eb_dict as ed
import eb_pv as pv
from eb_dict.meta import inline_refs as dict_inline_refs
from eb_pv import Atomic
from eb_pv.meta import inline_refs as pv_inline_refs
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shapes (PV) ──────────────────────────────────────────────────────────────


class PVL7(Shape):
    a = pv.IntRef.slot()
    b = pv.IntRef.slot()
    c = pv.IntRef.slot()
    d = pv.IntRef.slot()


class PVL6(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL7)


class PVL5(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL6)


class PVL4(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL5)


class PVL3(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL4)


class PVL2(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL3)


class PVL1(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL2)


class PVL0(Shape):
    child = pv.ShapesDictRef.slot(shape_type=PVL1)


# ── Shapes (dict) ────────────────────────────────────────────────────────────


class DL7(Shape):
    a = ed.IntRef.slot()
    b = ed.IntRef.slot()
    c = ed.IntRef.slot()
    d = ed.IntRef.slot()


class DL6(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL7)


class DL5(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL6)


class DL4(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL5)


class DL3(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL4)


class DL2(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL3)


class DL1(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL2)


class DL0(Shape):
    child = ed.ShapesDictRef.slot(shape_type=DL1)


# ── Path to leaf ─────────────────────────────────────────────────────────────

# PV: L0.child["k0"].child["k1"]...child["k6"].{a,b,c,d}
_pv_leaf = PVL0.child["k0"].child["k1"].child["k2"].child["k3"].child["k4"].child["k5"].child["k6"]
_d_leaf = DL0.child["k0"].child["k1"].child["k2"].child["k3"].child["k4"].child["k5"].child["k6"]

NUM_FIELDS = 4
KEYS = ["k0", "k1", "k2", "k3", "k4", "k5", "k6"]


# ── Pure Python dict ─────────────────────────────────────────────────────────


def _make_nested() -> dict:
    """Build nested dict structure matching shape hierarchy."""
    d: dict = {}
    cur = d
    for k in KEYS:
        cur.setdefault("child", {})[k] = {}
        cur = cur["child"][k]
    cur["a"] = 0
    cur["b"] = 1
    cur["c"] = 2
    cur["d"] = 3
    return d


def py_write(data: dict) -> None:
    cur = data
    for k in KEYS:
        cur = cur["child"][k]
    cur["a"] = 10
    cur["b"] = 11
    cur["c"] = 12
    cur["d"] = 13


def py_read(data: dict) -> None:
    cur = data
    for k in KEYS:
        cur = cur["child"][k]
    _ = cur["a"], cur["b"], cur["c"], cur["d"]


# ── Trees ────────────────────────────────────────────────────────────────────

# PV
_pv_write = Seq(
    _pv_leaf.a.set(10),
    _pv_leaf.b.set(11),
    _pv_leaf.c.set(12),
    _pv_leaf.d.set(13),
)
_pv_read = Seq(
    _pv_leaf.a.get(),
    _pv_leaf.b.get(),
    _pv_leaf.c.get(),
    _pv_leaf.d.get(),
)

pv_write_at = Atomic(_pv_write)
pv_read_at = Atomic(_pv_read)
pv_write_ai = pv_inline_refs(Atomic(_pv_write))
pv_read_ai = pv_inline_refs(Atomic(_pv_read))

# everydict
d_write = Seq(
    _d_leaf.a.set(10),
    _d_leaf.b.set(11),
    _d_leaf.c.set(12),
    _d_leaf.d.set(13),
)
d_read = Seq(
    _d_leaf.a.get(),
    _d_leaf.b.get(),
    _d_leaf.c.get(),
    _d_leaf.d.get(),
)
di_write = dict_inline_refs(d_write)
di_read = dict_inline_refs(d_read)

# Seed trees (need to set values before reading)
_pv_seed = Atomic(
    Seq(
        _pv_leaf.a.set(0),
        _pv_leaf.b.set(1),
        _pv_leaf.c.set(2),
        _pv_leaf.d.set(3),
    )
)
_d_seed = Seq(
    _d_leaf.a.set(0),
    _d_leaf.b.set(1),
    _d_leaf.c.set(2),
    _d_leaf.d.set(3),
)
_di_seed = dict_inline_refs(_d_seed)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 2000  # iterations


def _bench_pure_dict(label: str, fn, setup_data: dict) -> TimingResult:
    fn(setup_data)  # warmup
    t0 = time.perf_counter()
    for _ in range(N):
        fn(setup_data)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * NUM_FIELDS, counters={})


async def _bench_pv(label: str, tree, seed_tree) -> TimingResult:
    tmpdir = tempfile.mkdtemp(prefix="bench_deep_")
    try:
        from eb_pv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await seed_tree.execute(ctx)
            get_counters().reset()
            with timed_run(label, N * NUM_FIELDS) as results:
                for _ in range(N):
                    await tree.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def _bench_dict(label: str, tree, seed_tree) -> TimingResult:
    data: dict = {}
    ctx = Context().bind(data, dict, DL0)
    await seed_tree.execute(ctx)
    get_counters().reset()
    with timed_run(label, N * NUM_FIELDS) as results:
        for _ in range(N):
            await tree.execute(ctx)
    return results[0]


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    # Pure dict
    nested = _make_nested()
    results.append(_bench_pure_dict("write pure dict", py_write, nested))
    results.append(_bench_pure_dict("read pure dict", py_read, nested))

    # PV Atomic
    results.append(await _bench_pv("write PV Atomic", pv_write_at, _pv_seed))
    results.append(await _bench_pv("read PV Atomic", pv_read_at, _pv_seed))

    # PV Atomic+inline
    results.append(await _bench_pv("write PV Atomic+inline", pv_write_ai, _pv_seed))
    results.append(await _bench_pv("read PV Atomic+inline", pv_read_ai, _pv_seed))

    # everydict
    results.append(await _bench_dict("write everydict", d_write, _d_seed))
    results.append(await _bench_dict("read everydict", d_read, _d_seed))

    # everydict+inline
    results.append(await _bench_dict("write everydict+inline", di_write, _di_seed))
    results.append(await _bench_dict("read everydict+inline", di_read, _di_seed))

    uninstall_counters()
    print_results("Scenario: Deep Nesting (depth=8, 4 fields)", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
