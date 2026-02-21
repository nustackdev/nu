"""Layer-by-Layer Overhead — from raw rdbpy to term trees.

Single-file benchmark that measures put/get at every abstraction layer:
  L0  raw rdbpy binary put/get (C++ bindings, zero Python overhead)
  L1  tkv RocksDBStorage put/get (codec, tuple keys, transaction wrapper)
  L2  pv Container put_child_primitive / get_child_primitive
  L3  pv DictView __setitem__ / __getitem__
  L4  Shape/Ref via Atomic (term tree, span open/close)

Each layer builds on the previous. The report makes the per-layer cost delta
explicit so we can see exactly where overhead lives.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, "benchmarks")

import rdbpy
from tkv.tkv.storage import StorageProtocol
from utils import (
    TimingResult,
    format_counter_table,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)

import everypv as pv
from everybase import Context
from everypv import Atomic
from everyshape import Shape


# ============================================================================
# CONFIG
# ============================================================================

N = 500  # ops per benchmark (enough for stable μs-level timings)
VALUE = 42  # integer value written/read
VALUE_B = b"42"  # same as raw bytes


# ============================================================================
# L0: Raw rdbpy — binary put/get on TransactionDB
# ============================================================================


def bench_l0_put(n: int) -> TimingResult:
    """L0: raw rdbpy txn.put(bytes, bytes) — one key per txn."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        get_counters().reset()
        with timed_run(f"L0 rdbpy put x{n}", n) as results:
            for i in range(n):
                txn = db.begin_transaction()
                txn.put(f"k:{i}".encode(), VALUE_B)
                txn.commit()
                txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l0_get(n: int) -> TimingResult:
    """L0: raw rdbpy txn.get(bytes) — one key per txn."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        # Seed
        txn = db.begin_transaction()
        for i in range(n):
            txn.put(f"k:{i}".encode(), VALUE_B)
        txn.commit()
        txn.close()

        get_counters().reset()
        with timed_run(f"L0 rdbpy get x{n}", n) as results:
            for i in range(n):
                txn = db.begin_transaction()
                txn.get(f"k:{i}".encode())
                txn.rollback()
                txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# L1: TKV RocksDBStorage — tuple keys, codec, observer
# ============================================================================


def bench_l1_put(n: int) -> TimingResult:
    """L1: tkv storage transaction put — tuple key, codec encode, one key per txn."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"L1 tkv put x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(("/", "k", str(i)), VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l1_get(n: int) -> TimingResult:
    """L1: tkv storage snapshot get — tuple key, codec decode."""
    from tkv.codecs import BinaryCodec
    from tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed
            with storage.transaction() as tx:
                for i in range(n):
                    tx.put(("/", "k", str(i)), VALUE)

            get_counters().reset()
            with timed_run(f"L1 tkv get x{n}", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    snap.get(("/", "k", str(i)))
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# L2: PV Container — create_container + put_child_primitive / get_child_primitive
# ============================================================================


def bench_l2_put(n: int) -> TimingResult:
    """L2: pv container put_child_primitive — container marker, node ops."""
    from pv.container.container import Container
    from pv.container.container_ops import create_container
    from pv.container.types import ContainerProtocol, ContainerStructure

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            # Warm up: create root container
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
            get_counters().reset()

            with timed_run(f"L2 container put x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = Container.get(("/",), tx)
                        root.put_child_primitive(f"k{i}", VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l2_get(n: int) -> TimingResult:
    """L2: pv container get_child_primitive."""
    from pv.container.container import Container
    from pv.container.container_ops import create_container
    from pv.container.types import ContainerProtocol, ContainerStructure

    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            # Seed
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
                root = Container.get(("/",), tx)
                for i in range(n):
                    root.put_child_primitive(f"k{i}", VALUE)

            get_counters().reset()
            with timed_run(f"L2 container get x{n}", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    root = Container.get(("/",), snap)
                    root.get_child_primitive(f"k{i}")
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# L3: PV DictView — __setitem__ / __getitem__
# ============================================================================


def bench_l3_put(n: int) -> TimingResult:
    """L3: DictView['key'] = value — ensure_created, metadata, setitem."""
    from everypv.adapters.storage import rocksdb_storage_inmemory
    from everypv.views import DictView

    tmpdir = tempfile.mkdtemp(prefix="bench_l3_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            # Warm up: create root
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                root["_warmup"] = 0

            get_counters().reset()
            with timed_run(f"L3 dictview put x{n}", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = DictView.open_root(tx)
                        root[f"k{i}"] = VALUE
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l3_get(n: int) -> TimingResult:
    """L3: DictView['key'] — getitem with node_info checks."""
    from everypv.adapters.storage import rocksdb_storage_inmemory
    from everypv.views import DictView

    tmpdir = tempfile.mkdtemp(prefix="bench_l3_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            # Seed
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                for i in range(n):
                    root[f"k{i}"] = VALUE

            get_counters().reset()
            with timed_run(f"L3 dictview get x{n}", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    root = DictView.open_root(snap)
                    _ = root[f"k{i}"]
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# L4: Shape/Ref via Atomic — term tree + span
# ============================================================================


class FlatShape(Shape):
    value = pv.IntRef.slot()


async def bench_l4_put(n: int) -> TimingResult:
    """L4: Atomic(Shape.field.set(v)).execute() — pre-built term, only execution timed."""
    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l4_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            term = Atomic(FlatShape.value.set(VALUE))
            # Warm up
            await term.execute(ctx)

            get_counters().reset()
            with timed_run(f"L4 shape put x{n}", n) as results:
                for _ in range(n):
                    await term.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_l4_get(n: int) -> TimingResult:
    """L4: Atomic(Shape.field.get()).execute() — pre-built term, only execution timed."""
    from everypv.adapters.storage import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l4_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().with_handle(StorageProtocol, storage)
            # Seed
            await Atomic(FlatShape.value.set(VALUE)).execute(ctx)

            term = Atomic(FlatShape.value.get())
            get_counters().reset()
            with timed_run(f"L4 shape get x{n}", n) as results:
                for _ in range(n):
                    await term.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# Runner + Report
# ============================================================================


async def run_all() -> None:
    install_counters()

    # --- L0 (no counters needed, rdbpy is below tkv instrumentation) ---
    r_l0_put = bench_l0_put(N)
    r_l0_get = bench_l0_get(N)

    # --- L1 ---
    r_l1_put = bench_l1_put(N)
    r_l1_get = bench_l1_get(N)

    # --- L2 ---
    r_l2_put = bench_l2_put(N)
    r_l2_get = bench_l2_get(N)

    # --- L3 ---
    r_l3_put = bench_l3_put(N)
    r_l3_get = bench_l3_get(N)

    # --- L4 ---
    r_l4_put = await bench_l4_put(N)
    r_l4_get = await bench_l4_get(N)

    uninstall_counters()

    # Collect layer results for summary
    put_layers = [r_l0_put, r_l1_put, r_l2_put, r_l3_put, r_l4_put]
    get_layers = [r_l0_get, r_l1_get, r_l2_get, r_l3_get, r_l4_get]

    # ---- Print to stdout ----
    print_results("Layer-by-Layer PUT", put_layers)
    print_results("Layer-by-Layer GET", get_layers)

    # ---- Generate markdown report ----
    lines = []
    lines.append("# Layer-by-Layer Overhead (L0-L4)\n")
    lines.append(f"N = {N} ops per benchmark\n")

    # -- PUT summary --
    lines.append("## PUT — layer progression\n")
    lines.append(_layer_table(put_layers, r_l0_put))
    lines.append("")

    # -- GET summary --
    lines.append("## GET — layer progression\n")
    lines.append(_layer_table(get_layers, r_l0_get))
    lines.append("")

    # -- Counter details --
    lines.append("## PUT counters\n")
    lines.append(format_counter_table(put_layers))
    lines.append("")
    lines.append("## GET counters\n")
    lines.append(format_counter_table(get_layers))
    lines.append("")

    # -- Interpretation --
    lines.append("## Interpretation\n")
    lines.append("Each layer row shows:")
    lines.append("- **per-op (ms)**: average wall time per single put or get")
    lines.append("- **vs L0**: slowdown factor relative to raw rdbpy")
    lines.append("- **delta (ms)**: marginal cost added by *this* layer alone")
    lines.append("")
    lines.append("The delta column reveals where overhead actually lives.")

    report = "\n".join(lines)
    print("\n" + report)

    # Write report file
    Path("benchmarks/RESULTS_LAYERS.md").write_text(report + "\n")
    print("\n(Report written to benchmarks/RESULTS_LAYERS.md)")


def _layer_table(results: list[TimingResult], baseline: TimingResult) -> str:
    """Format a layer-progression table with deltas and ratios."""
    lines = []
    lines.append("| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |")
    lines.append("|-------|----------|-------------|-------|-------|------------|")
    prev_ms = 0.0
    base_ms = baseline.per_op_ms
    for i, r in enumerate(results):
        ratio = r.per_op_ms / base_ms if base_ms > 0 else 0
        delta = r.per_op_ms - prev_ms
        lines.append(
            f"| L{i} | {r.name} | {r.per_op_ms:.4f} | {r.ops_per_sec:,.0f} | "
            f"{ratio:.1f}x | +{delta:.4f} |"
        )
        prev_ms = r.per_op_ms
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(run_all())
