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
  nu-mem        -- plain dict substrate
  nu-mem+inline -- nu-mem with inline_refs deformation

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

import nu_mem as ed
import nu_virtuals as ebv
from nu import Context
from nu.abc import Seq
from nu.shape import Shape
from nu_mem.tree import inline_refs as dict_inline_refs
from nu_virtuals import Atomic
from nu_virtuals.tree import inline_refs as v_inline_refs
from virtuals.tkv.storage import StorageProtocol


# ── Shapes (PV) ──────────────────────────────────────────────────────────────


class VL7(Shape):
    a = ebv.IntRef.slot()
    b = ebv.IntRef.slot()
    c = ebv.IntRef.slot()
    d = ebv.IntRef.slot()


class VL6(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL7)


class VL5(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL6)


class VL4(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL5)


class VL3(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL4)


class VL2(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL3)


class VL1(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL2)


class VL0(Shape):
    child = ebv.ShapesDictRef.slot(shape_type=VL1)


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
_v_leaf = VL0.child["k0"].child["k1"].child["k2"].child["k3"].child["k4"].child["k5"].child["k6"]
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
_v_write = Seq(
    _v_leaf.a.store(10),
    _v_leaf.b.store(11),
    _v_leaf.c.store(12),
    _v_leaf.d.store(13),
)
_v_read = Seq(
    _v_leaf.a,
    _v_leaf.b,
    _v_leaf.c,
    _v_leaf.d,
)

v_write_at = Atomic(_v_write)
v_read_at = Atomic(_v_read)
v_write_ai = v_inline_refs(Atomic(_v_write))
v_read_ai = v_inline_refs(Atomic(_v_read))

# nu-mem
d_write = Seq(
    _d_leaf.a.store(10),
    _d_leaf.b.store(11),
    _d_leaf.c.store(12),
    _d_leaf.d.store(13),
)
d_read = Seq(
    _d_leaf.a,
    _d_leaf.b,
    _d_leaf.c,
    _d_leaf.d,
)
di_write = dict_inline_refs(d_write)
di_read = dict_inline_refs(d_read)

# Seed trees (need to set values before reading)
_v_seed = Atomic(
    Seq(
        _v_leaf.a.store(0),
        _v_leaf.b.store(1),
        _v_leaf.c.store(2),
        _v_leaf.d.store(3),
    )
)
_d_seed = Seq(
    _d_leaf.a.store(0),
    _d_leaf.b.store(1),
    _d_leaf.c.store(2),
    _d_leaf.d.store(3),
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


async def _bench_v(label: str, tree, seed_tree) -> TimingResult:
    tmpdir = tempfile.mkdtemp(prefix="bench_deep_")
    try:
        from nu_virtuals.presets import rocksdb_storage_inmemory

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
    results.append(await _bench_v("write virtuals Atomic", v_write_at, _v_seed))
    results.append(await _bench_v("read virtuals Atomic", v_read_at, _v_seed))

    # PV Atomic+inline
    results.append(await _bench_v("write virtuals Atomic+inline", v_write_ai, _v_seed))
    results.append(await _bench_v("read virtuals Atomic+inline", v_read_ai, _v_seed))

    # nu-mem
    results.append(await _bench_dict("write nu-mem", d_write, _d_seed))
    results.append(await _bench_dict("read nu-mem", d_read, _d_seed))

    # nu-mem+inline
    results.append(await _bench_dict("write nu-mem+inline", di_write, _di_seed))
    results.append(await _bench_dict("read nu-mem+inline", di_read, _di_seed))

    uninstall_counters()
    print_results("Scenario: Deep Nesting (depth=8, 4 fields)", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
