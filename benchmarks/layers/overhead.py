"""Layer-by-Layer Overhead -- pure execution cost at each abstraction layer.

Two measurement modes:

  Mode A: Pure R/W (1 txn, N ops)
    Transaction opened ONCE, N ops inside, commit ONCE.
    Isolates the pure per-layer read/write cost.

  Mode B: Per-op cost (N txns, N ops)
    One transaction per operation -- measures real-world per-op cost
    including transaction open/close/commit overhead.

Layers:
  L0  raw rdbpy binary put/get (C++ bindings, zero Python overhead)
  L1  tkv RocksDBStorage put/get (codec, tuple keys, transaction wrapper)
  L2  virtuals Container put_child_primitive / get_child_primitive
  L3  virtuals DictView __setitem__ / __getitem__
  L4  Shape/Ref via Atomic (term tree execution, span open/close)

Keys and term trees are pre-built before any timed section.
Benchmark loops measure only execution -- no construction overhead.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rdbpy
from utils import (
    TimingResult,
    get_counters,
    install_counters,
    print_results,
    timed_run,
    uninstall_counters,
)
from virtuals.tkv.storage import StorageProtocol

import eb_virtuals as ebv
from eb_virtuals import Atomic
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ============================================================================
# CONFIG
# ============================================================================

N_SIZES = [100, 1_000, 10_000]
N_MAX = max(N_SIZES)
VALUE = 42
VALUE_B = b"42"


# ============================================================================
# PRE-BUILT KEYS & TERMS
#
# Everything needed for the benchmark loops is constructed here, once.
# Pre-built to N_MAX; benchmarks slice to the requested n.
# ============================================================================


class FlatShape(Shape):
    value = ebv.IntRef.slot()


# L0: raw bytes keys
L0_KEYS = [f"k:{i}".encode() for i in range(N_MAX)]

# L1: tkv tuple keys
L1_KEYS = [("/", "k", str(i)) for i in range(N_MAX)]

# L2/L3: string keys
STR_KEYS = [f"k{i}" for i in range(N_MAX)]

# L4: pre-built term trees (Mode B -- single op per Atomic)
L4_PUT = Atomic(FlatShape.value.store(VALUE))
L4_GET = Atomic(FlatShape.value)
L4_SEED = Atomic(FlatShape.value.store(VALUE))


def _build_l4_batched(n: int) -> tuple[Atomic, Atomic]:
    """Build Mode A batched terms for a given N."""
    put = Atomic(Seq(*[FlatShape.value.store(VALUE) for _ in range(n)]))
    get = Atomic(Seq(*[FlatShape.value for _ in range(n)]))
    return put, get


# ============================================================================
# MODE A: Pure R/W (1 txn, N ops)
#
# Transaction opened ONCE before the loop, closed ONCE after.
# The ONLY variable between layers is the layer's own code path.
# ============================================================================


def bench_l0_put_a(n: int) -> TimingResult:
    """L0 Mode A: raw rdbpy -- 1 txn, N puts."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0a_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        get_counters().reset()
        with timed_run(f"L0 rdbpy put x{n} [1txn]", n) as results:
            txn = db.begin_transaction()
            for i in range(n):
                txn.put(L0_KEYS[i], VALUE_B)
            txn.commit()
            txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l0_get_a(n: int) -> TimingResult:
    """L0 Mode A: raw rdbpy -- 1 snapshot, N gets."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0a_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        # Seed
        txn = db.begin_transaction()
        for i in range(n):
            txn.put(L0_KEYS[i], VALUE_B)
        txn.commit()
        txn.close()

        get_counters().reset()
        with timed_run(f"L0 rdbpy get x{n} [1snap]", n) as results:
            txn = db.begin_transaction()
            for i in range(n):
                txn.get(L0_KEYS[i])
            txn.rollback()
            txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l1_put_a(n: int) -> TimingResult:
    """L1 Mode A: tkv storage -- 1 txn, N puts."""
    from virtuals.tkv.codecs import BinaryCodec
    from virtuals.tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1a_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"L1 tkv put x{n} [1txn]", n) as results:
                with storage.transaction() as tx:
                    for i in range(n):
                        tx.put(L1_KEYS[i], VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l1_get_a(n: int) -> TimingResult:
    """L1 Mode A: tkv storage -- 1 snapshot, N gets."""
    from virtuals.tkv.codecs import BinaryCodec
    from virtuals.tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1a_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed
            with storage.transaction() as tx:
                for i in range(n):
                    tx.put(L1_KEYS[i], VALUE)

            get_counters().reset()
            with timed_run(f"L1 tkv get x{n} [1snap]", n) as results:
                snap = storage.begin_snapshot()
                for i in range(n):
                    snap.get(L1_KEYS[i])
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l2_put_a(n: int) -> TimingResult:
    """L2 Mode A: virtuals container -- 1 txn, N puts."""
    from virtuals.container.container import Container
    from virtuals.container.container_ops import create_container
    from virtuals.container.types import ContainerProtocol, ContainerStructure

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
            get_counters().reset()

            with timed_run(f"L2 container put x{n} [1txn]", n) as results:
                with storage.transaction() as tx:
                    root = Container.get(("/",), tx)
                    for i in range(n):
                        root.put_child_primitive(STR_KEYS[i], VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l2_get_a(n: int) -> TimingResult:
    """L2 Mode A: virtuals container -- 1 snapshot, N gets."""
    from virtuals.container.container import Container
    from virtuals.container.container_ops import create_container
    from virtuals.container.types import ContainerProtocol, ContainerStructure

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
                root = Container.get(("/",), tx)
                for i in range(n):
                    root.put_child_primitive(STR_KEYS[i], VALUE)

            get_counters().reset()
            with timed_run(f"L2 container get x{n} [1snap]", n) as results:
                snap = storage.begin_snapshot()
                root = Container.get(("/",), snap)
                for i in range(n):
                    root.get_child_primitive(STR_KEYS[i])
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l3_put_a(n: int) -> TimingResult:
    """L3 Mode A: DictView -- 1 txn, N puts."""
    from virtuals.views import DictView

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l3a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                root["_warmup"] = 0

            get_counters().reset()
            with timed_run(f"L3 dictview put x{n} [1txn]", n) as results:
                with storage.transaction() as tx:
                    root = DictView.open_root(tx)
                    for i in range(n):
                        root[STR_KEYS[i]] = VALUE
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l3_get_a(n: int) -> TimingResult:
    """L3 Mode A: DictView -- 1 snapshot, N gets."""
    from virtuals.views import DictView

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l3a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                for i in range(n):
                    root[STR_KEYS[i]] = VALUE

            get_counters().reset()
            with timed_run(f"L3 dictview get x{n} [1snap]", n) as results:
                snap = storage.begin_snapshot()
                root = DictView.open_root(snap)
                for i in range(n):
                    _ = root[STR_KEYS[i]]
                snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_l4_put_a(n: int) -> TimingResult:
    """L4 Mode A: Atomic(Seq(*N writes)) -- single txn, N ops."""
    from eb_virtuals.presets import rocksdb_storage_inmemory

    l4_put_batched, _ = _build_l4_batched(n)
    tmpdir = tempfile.mkdtemp(prefix="bench_l4a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await L4_PUT.execute(ctx)  # warm up

            get_counters().reset()
            with timed_run(f"L4 shape put x{n} [1txn]", n) as results:
                await l4_put_batched.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_l4_get_a(n: int) -> TimingResult:
    """L4 Mode A: Atomic(Seq(*N reads)) -- single snapshot, N ops."""
    from eb_virtuals.presets import rocksdb_storage_inmemory

    _, l4_get_batched = _build_l4_batched(n)
    tmpdir = tempfile.mkdtemp(prefix="bench_l4a_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await L4_SEED.execute(ctx)  # seed data

            get_counters().reset()
            with timed_run(f"L4 shape get x{n} [1snap]", n) as results:
                await l4_get_batched.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# MODE B: Per-op cost (N txns, N ops)
#
# One transaction per operation. Includes transaction overhead.
# This is what real-world single-op usage looks like.
# ============================================================================


def bench_l0_put_b(n: int) -> TimingResult:
    """L0 Mode B: raw rdbpy -- 1 txn per put."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0b_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        get_counters().reset()
        with timed_run(f"L0 rdbpy put x{n} [1txn/op]", n) as results:
            for i in range(n):
                txn = db.begin_transaction()
                txn.put(L0_KEYS[i], VALUE_B)
                txn.commit()
                txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l0_get_b(n: int) -> TimingResult:
    """L0 Mode B: raw rdbpy -- 1 txn per get."""
    tmpdir = tempfile.mkdtemp(prefix="bench_l0b_")
    try:
        opts = rdbpy.Options(create_if_missing=True)
        db = rdbpy.TransactionDB(tmpdir, opts)

        # Seed
        txn = db.begin_transaction()
        for i in range(n):
            txn.put(L0_KEYS[i], VALUE_B)
        txn.commit()
        txn.close()

        get_counters().reset()
        with timed_run(f"L0 rdbpy get x{n} [1snap/op]", n) as results:
            for i in range(n):
                txn = db.begin_transaction()
                txn.get(L0_KEYS[i])
                txn.rollback()
                txn.close()

        db.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l1_put_b(n: int) -> TimingResult:
    """L1 Mode B: tkv storage -- 1 txn per put."""
    from virtuals.tkv.codecs import BinaryCodec
    from virtuals.tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1b_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            get_counters().reset()
            with timed_run(f"L1 tkv put x{n} [1txn/op]", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        tx.put(L1_KEYS[i], VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l1_get_b(n: int) -> TimingResult:
    """L1 Mode B: tkv storage -- 1 snapshot per get."""
    from virtuals.tkv.codecs import BinaryCodec
    from virtuals.tkv.storages.rocksdb import RocksDBStorage

    tmpdir = tempfile.mkdtemp(prefix="bench_l1b_")
    try:
        with RocksDBStorage(path=tmpdir, codec=BinaryCodec(), observer=None) as storage:
            # Seed
            with storage.transaction() as tx:
                for i in range(n):
                    tx.put(L1_KEYS[i], VALUE)

            get_counters().reset()
            with timed_run(f"L1 tkv get x{n} [1snap/op]", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    snap.get(L1_KEYS[i])
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l2_put_b(n: int) -> TimingResult:
    """L2 Mode B: virtuals container -- 1 txn per put (includes Container.get)."""
    from virtuals.container.container import Container
    from virtuals.container.container_ops import create_container
    from virtuals.container.types import ContainerProtocol, ContainerStructure

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
            get_counters().reset()

            with timed_run(f"L2 container put x{n} [1txn/op]", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = Container.get(("/",), tx)
                        root.put_child_primitive(STR_KEYS[i], VALUE)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l2_get_b(n: int) -> TimingResult:
    """L2 Mode B: virtuals container -- 1 snapshot per get (includes Container.get)."""
    from virtuals.container.container import Container
    from virtuals.container.container_ops import create_container
    from virtuals.container.types import ContainerProtocol, ContainerStructure

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l2b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                create_container(
                    ("/",),
                    ContainerStructure(1),
                    ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
                    tx,
                )
                root = Container.get(("/",), tx)
                for i in range(n):
                    root.put_child_primitive(STR_KEYS[i], VALUE)

            get_counters().reset()
            with timed_run(f"L2 container get x{n} [1snap/op]", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    root = Container.get(("/",), snap)
                    root.get_child_primitive(STR_KEYS[i])
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l3_put_b(n: int) -> TimingResult:
    """L3 Mode B: DictView -- 1 txn per put (includes open_root)."""
    from virtuals.views import DictView

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l3b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                root["_warmup"] = 0

            get_counters().reset()
            with timed_run(f"L3 dictview put x{n} [1txn/op]", n) as results:
                for i in range(n):
                    with storage.transaction() as tx:
                        root = DictView.open_root(tx)
                        root[STR_KEYS[i]] = VALUE
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


def bench_l3_get_b(n: int) -> TimingResult:
    """L3 Mode B: DictView -- 1 snapshot per get (includes open_root)."""
    from virtuals.views import DictView

    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l3b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            with storage.transaction() as tx:
                root = DictView.open_root(tx)
                for i in range(n):
                    root[STR_KEYS[i]] = VALUE

            get_counters().reset()
            with timed_run(f"L3 dictview get x{n} [1snap/op]", n) as results:
                for i in range(n):
                    snap = storage.begin_snapshot()
                    root = DictView.open_root(snap)
                    _ = root[STR_KEYS[i]]
                    snap.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_l4_put_b(n: int) -> TimingResult:
    """L4 Mode B: Atomic(Shape.field.store(v)).execute() -- 1 txn per op."""
    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l4b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await L4_PUT.execute(ctx)  # warm up

            get_counters().reset()
            with timed_run(f"L4 shape put x{n} [1txn/op]", n) as results:
                for _ in range(n):
                    await L4_PUT.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


async def bench_l4_get_b(n: int) -> TimingResult:
    """L4 Mode B: Atomic(Shape.field).execute() -- 1 snapshot per op."""
    from eb_virtuals.presets import rocksdb_storage_inmemory

    tmpdir = tempfile.mkdtemp(prefix="bench_l4b_")
    try:
        with rocksdb_storage_inmemory(tmpdir) as storage:
            ctx = Context().bind(storage, StorageProtocol)
            await L4_SEED.execute(ctx)  # seed data

            get_counters().reset()
            with timed_run(f"L4 shape get x{n} [1snap/op]", n) as results:
                for _ in range(n):
                    await L4_GET.execute(ctx)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return results[0]


# ============================================================================
# Runner + Report
# ============================================================================


async def _run_n(n: int) -> dict:
    """Run Mode A + Mode B for a given N, return results dict."""
    a_l0_put = bench_l0_put_a(n)
    a_l0_get = bench_l0_get_a(n)
    a_l1_put = bench_l1_put_a(n)
    a_l1_get = bench_l1_get_a(n)
    a_l2_put = bench_l2_put_a(n)
    a_l2_get = bench_l2_get_a(n)
    a_l3_put = bench_l3_put_a(n)
    a_l3_get = bench_l3_get_a(n)
    a_l4_put = await bench_l4_put_a(n)
    a_l4_get = await bench_l4_get_a(n)

    b_l0_put = bench_l0_put_b(n)
    b_l0_get = bench_l0_get_b(n)
    b_l1_put = bench_l1_put_b(n)
    b_l1_get = bench_l1_get_b(n)
    b_l2_put = bench_l2_put_b(n)
    b_l2_get = bench_l2_get_b(n)
    b_l3_put = bench_l3_put_b(n)
    b_l3_get = bench_l3_get_b(n)
    b_l4_put = await bench_l4_put_b(n)
    b_l4_get = await bench_l4_get_b(n)

    return {
        "a_put": [a_l0_put, a_l1_put, a_l2_put, a_l3_put, a_l4_put],
        "a_get": [a_l0_get, a_l1_get, a_l2_get, a_l3_get, a_l4_get],
        "b_put": [b_l0_put, b_l1_put, b_l2_put, b_l3_put, b_l4_put],
        "b_get": [b_l0_get, b_l1_get, b_l2_get, b_l3_get, b_l4_get],
    }


async def run_all() -> None:
    install_counters()

    all_runs: dict[int, dict] = {}
    for n in N_SIZES:
        print(f"\n>>> N = {n:,}")
        all_runs[n] = await _run_n(n)

    uninstall_counters()

    # ---- Print to stdout ----
    for n, d in all_runs.items():
        print_results(f"N={n:,} Mode A PUT (1 txn)", d["a_put"])
        print_results(f"N={n:,} Mode A GET (1 snap)", d["a_get"])
        print_results(f"N={n:,} Mode B PUT (1 txn/op)", d["b_put"])
        print_results(f"N={n:,} Mode B GET (1 snap/op)", d["b_get"])

    # ---- Generate markdown report ----
    lines = []
    lines.append("# Layer-by-Layer Overhead (L0-L4)\n")
    lines.append(f"N sizes: {', '.join(f'{n:,}' for n in N_SIZES)}\n")

    for n, d in all_runs.items():
        lines.append(f"## N = {n:,}\n")

        lines.append("### Mode A: Pure R/W (1 txn, N ops)\n")
        lines.append("Transaction opened ONCE, all ops inside, commit ONCE.\n")

        lines.append("#### PUT\n")
        lines.append(_layer_table(d["a_put"], d["a_put"][0]))
        lines.append("")
        lines.append("#### GET\n")
        lines.append(_layer_table(d["a_get"], d["a_get"][0]))
        lines.append("")

        lines.append("### Mode B: Per-op cost (N txns, N ops)\n")
        lines.append("One txn per operation. Real-world single-op cost.\n")

        lines.append("#### PUT\n")
        lines.append(_layer_table(d["b_put"], d["b_put"][0]))
        lines.append("")
        lines.append("#### GET\n")
        lines.append(_layer_table(d["b_get"], d["b_get"][0]))
        lines.append("")

    lines.append("## Notes\n")
    lines.append("- L0 counters show 0 because rdbpy bypasses monkey-patched tkv layer")
    lines.append("- Layers are not strictly stacked: L4 (Shape) does NOT go through L3 (DictView)")
    lines.append("- Each layer uses its own API path, so deltas show marginal cost of that API")
    lines.append("- Mode A delta = pure code overhead; Mode B delta = code + txn overhead")

    report = "\n".join(lines)
    print("\n" + report)


def _layer_table(results: list[TimingResult], baseline: TimingResult) -> str:
    """Format a layer-progression table with vs-L0 ratio."""
    lines = []
    lines.append("| Layer | Scenario | per-op (ms) | ops/s | vs L0 |")
    lines.append("|-------|----------|-------------|-------|-------|")
    base_ms = baseline.per_op_ms
    for i, r in enumerate(results):
        ratio = r.per_op_ms / base_ms if base_ms > 0 else 0
        lines.append(
            f"| L{i} | {r.name} | {r.per_op_ms:.4f} | {r.ops_per_sec:,.0f} | {ratio:.1f}x |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(run_all())
