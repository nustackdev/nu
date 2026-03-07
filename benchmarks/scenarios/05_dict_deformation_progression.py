"""Scenario: Dict Deformation Progression -- same tree, cumulative optimizations.

Shows how inline_refs deformation improves everydict performance on a simple
User shape (name, age, email, score -- 4 scalar fields).

Realistic pattern: one tree execution per 4-field batch, repeated N times.

Progression:
  1. Raw everydict  -- Seq(ref.set/get)    standard morphisms + Ref parent-chains
  2. Inline refs    -- inline_refs          flatten Ref parent-chains to O(1) lookups

Dict substrate has no unsafe ops, no Transaction/Snapshot, no Init --
inline_refs is the only deformation available.
"""

from __future__ import annotations

import asyncio
import sys
import time


sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from utils import (
    TimingResult,
    print_results,
)

import eb_dict as ed
from eb_dict.meta import inline_refs
from everybase import Context
from everybase.abc import Seq
from everybase.shape import Shape


# ── Shape ─────────────────────────────────────────────────────────────────────


class User(Shape):
    name = ed.StrRef.slot()
    age = ed.IntRef.slot()
    email = ed.StrRef.slot()
    score = ed.FloatRef.slot()


FIELDS = [User.name, User.age, User.email, User.score]
NUM_FIELDS = len(FIELDS)
WRITE_VALUES = ["Alice", 30, "alice@example.com", 99.5]


# ── 1. Raw everydict — standard morphisms ────────────────────────────────────

raw_write = Seq(*[f.set(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)])
raw_read = Seq(*[f.get() for f in FIELDS])


# ── 2. Inline refs — inline_refs ─────────────────────────────────────────────

inline_write = inline_refs(Seq(*[f.set(v) for f, v in zip(FIELDS, WRITE_VALUES, strict=True)]))
inline_read = inline_refs(Seq(*[f.get() for f in FIELDS]))


# ── Pure Python dict baseline ────────────────────────────────────────────────


def py_write(data: dict) -> None:
    data["name"] = "Alice"
    data["age"] = 30
    data["email"] = "alice@example.com"
    data["score"] = 99.5


def py_read(data: dict) -> None:
    _ = data["name"], data["age"], data["email"], data["score"]


# ── Benchmarks ────────────────────────────────────────────────────────────────

N = 2000  # iterations (each = 1 tree execution with 4 field ops)


def _bench_pure_dict(label: str, fn, setup_fn) -> TimingResult:
    data: dict = {}
    setup_fn(data)
    fn(data)  # warmup
    t0 = time.perf_counter()
    for _ in range(N):
        fn(data)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * NUM_FIELDS, counters={})


async def _bench_dict(label: str, tree, seed_tree) -> TimingResult:
    data: dict = {}
    ctx = Context().bind(data, dict, User)
    await seed_tree.execute(ctx)
    t0 = time.perf_counter()
    for _ in range(N):
        await tree.execute(ctx)
    elapsed = time.perf_counter() - t0
    return TimingResult(name=label, wall_time_s=elapsed, n_ops=N * NUM_FIELDS, counters={})


# ── Runner ────────────────────────────────────────────────────────────────────


async def run_all() -> list[TimingResult]:
    results = []

    # Pure dict baseline
    results.append(_bench_pure_dict("write pure dict", py_write, py_write))
    results.append(_bench_pure_dict("read pure dict", py_read, py_write))

    # 1. Raw everydict
    results.append(await _bench_dict("write 1:raw", raw_write, raw_write))
    results.append(await _bench_dict("read 1:raw", raw_read, raw_write))

    # 2. Inline refs
    results.append(await _bench_dict("write 2:inline", inline_write, raw_write))
    results.append(await _bench_dict("read 2:inline", inline_read, raw_write))

    print_results("Dict Deformation Progression (4 fields, depth=1)", results)
    return results


if __name__ == "__main__":
    asyncio.run(run_all())
