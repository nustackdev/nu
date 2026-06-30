"""Scenario: Virtuals Deformation Progression -- same tree, cumulative optimizations.

Shows how each deformation layer improves virtuals performance on a simple
User shape (name, age, email, score -- 4 scalar fields).

Realistic pattern: one Transaction/Snapshot per 4-field batch, repeated N times.

Progression:
  1. Raw virtuals         -- Atomic(Seq(ref.store/load))           standard morphisms
  2. Unsafe ops     -- optimize_primitive_reads/writes     ItemLoad->UnsafeGet etc.
  3. Inline refs    -- inline_refs                         flatten Ref parent-chains
  4. Manual optimal -- Transaction + Init + ParentSkipSet  hand-built, no deformation

Each level builds on the previous. Level 4 is the theoretical floor for
virtuals trees -- a single Transaction span, one Init to materialize containers,
then ParentSkip writes/reads that each do a single ctx.put()/ctx.get().
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

import nu_virtuals as ebv
from nu import Context, replace
from nu.abc import Seq
from nu.shape import Shape
from nu_virtuals import (
    Atomic,
    InitItemCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    Snapshot,
    Transaction,
    optimize_primitive_reads,
    optimize_primitive_writes,
)
from nu_virtuals.morphisms.item import ItemPrimitiveSetUnsafeCmd
from nu_virtuals.tree import inline_refs
from virtuals.tkv.storage import StorageProtocol


# ── Shape ─────────────────────────────────────────────────────────────────────


class User(Shape):
    name = ebv.StrRef.slot()
    age = ebv.IntRef.slot()
    email = ebv.StrRef.slot()
    score = ebv.FloatRef.slot()


FIELDS = [User.name, User.age, User.email, User.score]
NUM_FIELDS = len(FIELDS)
WRITE_VALUES = ["Alice", 30, "alice@example.com", 99.5]


# ── 1. Raw virtuals — standard morphisms ───────────────────────────────────────────

raw_write = Atomic(Seq(*[f.store(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)]))
raw_read = Atomic(Seq(*FIELDS))


# ── 2. Unsafe ops — optimize_primitive_reads/writes ──────────────────────────

unsafe_write = optimize_primitive_writes(
    Atomic(Seq(*[f.store(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)]))
)
unsafe_read = optimize_primitive_reads(Atomic(Seq(*FIELDS)))


# ── 3. Inline refs — inline_refs ─────────────────────────────────────────────

inline_write = inline_refs(
    optimize_primitive_writes(
        Atomic(Seq(*[f.store(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)]))
    )
)
inline_read = inline_refs(optimize_primitive_reads(Atomic(Seq(*FIELDS))))


# ── 4. Manual optimal — Transaction + Init + ParentSkipSet ───────────────────
#
# Hand-built tree that represents the theoretical optimum for PV:
#   - Transaction (not Atomic) -- skip purity detection
#   - InitItemCmd once to materialize container chain
#   - ItemPrimitiveSetUnsafeParentSkipCmd -- single ctx.put() per field
#   - Snapshot for reads -- cheaper than Transaction
#
# All refs are inline_refs'd for flat path resolution.

_init_ref = FIELDS[0]  # any ref to materialize the User container chain

# Write: Transaction(Init + ParentSkipSet x 4)
_manual_write_unsafe = optimize_primitive_writes(
    Seq(*[f.store(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)])
)
_manual_write_parentskip = replace(
    _manual_write_unsafe,
    lambda n: isinstance(n, ItemPrimitiveSetUnsafeCmd),
    lambda n: ItemPrimitiveSetUnsafeParentSkipCmd(n.ref, n.value_expr),
)
_manual_write_inlined = inline_refs(_manual_write_parentskip)
_init_inlined = inline_refs(InitItemCmd(_init_ref))
manual_write = Transaction(Seq(_init_inlined, _manual_write_inlined))

# Read: Snapshot(UnsafeGet x 4) with inlined refs
_manual_read_unsafe = optimize_primitive_reads(Seq(*FIELDS))
_manual_read_inlined = inline_refs(_manual_read_unsafe)
manual_read = Snapshot(_manual_read_inlined)


# ── Pure Python dict baseline ────────────────────────────────────────────────


def py_write(data: dict) -> None:
    data["name"] = "Alice"
    data["age"] = 30
    data["email"] = "alice@example.com"
    data["score"] = 99.5


def py_read(data: dict) -> None:
    _ = data["name"], data["age"], data["email"], data["score"]


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 2000  # iterations (each = 1 transaction/snapshot with 4 field ops)


def _bench_pure_dict(label: str, fn, setup_fn) -> TimingResult:
    data: dict = {}
    setup_fn(data)
    fn(data)  # warmup
    t0 = time.perf_counter()
    for _ in range(N):
        fn(data)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * NUM_FIELDS, counters={})


async def _bench_v(label: str, tree, seed_tree) -> TimingResult:
    tmpdir = tempfile.mkdtemp(prefix="bench_deform_")
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


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    install_counters()
    results = []

    # Pure dict baseline
    results.append(_bench_pure_dict("write pure dict", py_write, py_write))
    results.append(_bench_pure_dict("read pure dict", py_read, py_write))

    # 1. Raw virtuals
    results.append(await _bench_v("write 1:raw", raw_write, raw_write))
    results.append(await _bench_v("read 1:raw", raw_read, raw_write))

    # 2. Unsafe ops
    results.append(await _bench_v("write 2:unsafe", unsafe_write, raw_write))
    results.append(await _bench_v("read 2:unsafe", unsafe_read, raw_write))

    # 3. Inline refs
    results.append(await _bench_v("write 3:inline", inline_write, raw_write))
    results.append(await _bench_v("read 3:inline", inline_read, raw_write))

    # 4. Manual optimal
    results.append(await _bench_v("write 4:manual", manual_write, raw_write))
    results.append(await _bench_v("read 4:manual", manual_read, raw_write))

    uninstall_counters()
    print_results("Virtuals Deformation Progression (4 fields, depth=1)", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
