"""Scenario: Flat Fields -- 1 shape, 4 fields, no nesting.

Simplest possible case: Shape.field.get() / .set() with depth=1 refs.
Measures pure framework overhead without any nesting navigation cost.
Each field op = 1 ref resolve + 1 morphism execute.

Modes:
  pure dict        -- imperative Python baseline
  PV Atomic        -- single Atomic wrapping entire Seq
  PV Atomic+inline -- PV with inline_refs deformation
  everydict        -- plain dict substrate
  everydict+inline -- everydict with inline_refs deformation

Benchmarks:
  write  -- set all 4 fields (N times)
  read   -- get all 4 fields (N times)
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import time


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import everydict as ed
from everydict.meta import inline_refs as dict_inline_refs
from tkv.tkv.storage import StorageProtocol
from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)

import everypv as pv
from everybase import Context
from everybase.abc import Seq
from everypv import Atomic
from everypv.meta import inline_refs as pv_inline_refs
from everyshape import Shape


# ── Shapes ────────────────────────────────────────────────────────────────────


class PVRecord(Shape):
    a = pv.IntRef.slot()
    b = pv.IntRef.slot()
    c = pv.IntRef.slot()
    d = pv.IntRef.slot()


class DRecord(Shape):
    a = ed.IntRef.slot()
    b = ed.IntRef.slot()
    c = ed.IntRef.slot()
    d = ed.IntRef.slot()


PV_FIELDS = [PVRecord.a, PVRecord.b, PVRecord.c, PVRecord.d]
D_FIELDS = [DRecord.a, DRecord.b, DRecord.c, DRecord.d]
NUM_FIELDS = 4


# ── Pure Python dict ─────────────────────────────────────────────────────────


def py_write(data: dict) -> None:
    data["a"] = 1
    data["b"] = 2
    data["c"] = 3
    data["d"] = 4


def py_read(data: dict) -> None:
    _ = data["a"], data["b"], data["c"], data["d"]


# ── Trees ────────────────────────────────────────────────────────────────────

# PV
_pv_write = Seq(*[f.set(i) for i, f in enumerate(PV_FIELDS)])
_pv_read = Seq(*[f.get() for f in PV_FIELDS])

pv_write_at = Atomic(_pv_write)
pv_read_at = Atomic(_pv_read)
pv_write_ai = pv_inline_refs(Atomic(_pv_write))
pv_read_ai = pv_inline_refs(Atomic(_pv_read))

# everydict
d_write = Seq(*[f.set(i) for i, f in enumerate(D_FIELDS)])
d_read = Seq(*[f.get() for f in D_FIELDS])
di_write = dict_inline_refs(d_write)
di_read = dict_inline_refs(d_read)


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 2000  # iterations (flat is fast, need more reps)


def _bench_pure_dict(label: str, fn, setup_fn) -> TimingResult:
    data: dict = {}
    setup_fn(data)
    fn(data)  # warmup
    t0 = time.perf_counter()
    for _ in range(N):
        fn(data)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * NUM_FIELDS, counters={})


async def _bench_pv(label: str, tree, seed_tree) -> TimingResult:
    tmpdir = tempfile.mkdtemp(prefix="bench_flat_")
    try:
        from everypv.adapters.storage import rocksdb_storage_inmemory

        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
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
    ctx = Context().with_handle(dict, data, scope=DRecord)
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
    results.append(_bench_pure_dict("write pure dict", py_write, py_write))
    results.append(_bench_pure_dict("read pure dict", py_read, py_write))

    # PV Atomic
    results.append(await _bench_pv("write PV Atomic", pv_write_at, pv_write_at))
    results.append(await _bench_pv("read PV Atomic", pv_read_at, pv_write_at))

    # PV Atomic+inline
    results.append(await _bench_pv("write PV Atomic+inline", pv_write_ai, pv_write_ai))
    results.append(await _bench_pv("read PV Atomic+inline", pv_read_ai, pv_write_ai))

    # everydict
    results.append(await _bench_dict("write everydict", d_write, d_write))
    results.append(await _bench_dict("read everydict", d_read, d_write))

    # everydict+inline
    results.append(await _bench_dict("write everydict+inline", di_write, di_write))
    results.append(await _bench_dict("read everydict+inline", di_read, di_write))

    uninstall_counters()
    print_results("Scenario: Flat Fields (depth=1, 4 fields)", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
