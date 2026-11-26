"""Context benchmark: the cost of handing values to bodies and of reading them back.

Not a test. The file name keeps pytest from collecting it, so the suite never
runs it. Run it by hand on red and compare its table across changes to the
context::

    uv run python tests/bench/bench_context.py            # 5 runs per case, median
    uv run python tests/bench/bench_context.py --runs 9

Cases:
    - 100k items through Map, ForEachDo, Filter, Accumulate, Reduce, each with
      a body that only reads what it is handed.
    - ForEachParAsync over 1k arms, the same trivial body.
    - One mem ref read and one fabric read, under 0 and 10 nested Provides,
      repeated in a loop and reported per read.

Every body is built in the ``bodies`` section below and nowhere else. When the
way a body reads its values changes, port that section and leave the rest.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from typing import TYPE_CHECKING

import nu
from nu.engine.structure import Declared
from nu.lang import ScalarAction
from nustd.functools.interactions import Reduce
from nustd.itertools.interactions import Accumulate


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


N_ITEMS = 100_000
N_ARMS = 1_000
N_READS = 100_000
DEPTH = 10


class Touch(ScalarAction):
    """Evaluates its child and drops the result: a flow body as cheap as a read.

    A flow body must be an action, so the read is wrapped in one. The declared
    mutation slot only satisfies validation; nothing is written.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, value: object) -> None:
        super().__init__(value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (value,) = children

        def thunk(rt: Runtime) -> None:
            value(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (value,) = children

        async def athunk(rt: Runtime) -> None:
            await value(rt)

        return athunk


# =============================================================================
# bodies: the only place that knows how a body reads its values
# =============================================================================


def one(x: object) -> object:
    """A body handed one value: reads it and nothing else."""
    return x


def two(acc: object, x: object) -> object:
    """A body handed two values (accumulator, item): reads the item."""
    return x


def read_one() -> Callable:
    """The one-value body slot a query takes (Map, Filter)."""
    return lambda x: one(x)


def act_one() -> Callable:
    """The one-value body slot a flow takes (ForEachDo, ForEachParAsync): an action."""
    return lambda x: Touch(one(x))


def read_two() -> Callable:
    """The two-value body slot an interaction takes."""
    return lambda acc, x: two(acc, x)


def repeat(n: int, value: object) -> object:
    """``value`` evaluated ``n`` times, the loop index unread."""
    return nu.ForRangeDo(0, n, lambda i: Touch(value))


class Held(nu.Shape):
    """The mem store the lookup case reads."""

    value = nu.IntRef.slot()


def held(body: object) -> object:
    """``body`` with ``Held`` bound in a frame of its own."""
    return nu.Frame(Held, body, value=1)


# =============================================================================
# trees
# =============================================================================


def _items() -> object:
    return nu.Iter(list(range(1, N_ITEMS + 1)))


def map_tree() -> object:
    return nu.Collect(nu.Map(_items(), read_one()))


def foreach_tree() -> object:
    return nu.ForEachDo(_items(), act_one())


def filter_tree() -> object:
    return nu.Collect(nu.Filter(_items(), read_one()))


def accumulate_tree() -> object:
    return nu.Collect(Accumulate(_items(), read_two()))


def reduce_tree() -> object:
    return Reduce(_items(), read_two())


def foreach_par_tree() -> object:
    return nu.ForEachParAsync(nu.Iter(list(range(N_ARMS))), act_one())


class Target:
    """The fabric the fabric-read case reads, provided above the stack."""


_PROVIDED = [type(f"Provided{i}", (), {}) for i in range(DEPTH)]


def stacked(depth: int, read: object) -> object:
    """``read`` evaluated in a loop, ``depth`` Provides below ``Held`` and ``Target``.

    Both stores the reads reach sit at the outside, so every Provide in
    between is a frame a lookup may have to pass on its way up.
    """
    body = repeat(N_READS, read)
    for cls in reversed(_PROVIDED[:depth]):
        body = nu.Provide(cls, body=body)
    return held(nu.Provide(Target, body=body))


def loop_tree(depth: int) -> object:
    """The read loop with nothing read: the overhead the read cases subtract."""
    return stacked(depth, nu.Literal(None))


def mem_read_tree(depth: int) -> object:
    """A mem ref read per iteration."""
    return stacked(depth, Held.value)


def fabric_read_tree(depth: int) -> object:
    """A fabric read per iteration."""
    return stacked(depth, nu.FabricRef(Target))


# =============================================================================
# timing
# =============================================================================


def _time_sync(build: Callable[[], object]) -> float:
    tree = build()
    start = time.perf_counter()
    nu.run(tree)
    return time.perf_counter() - start


def _time_async(build: Callable[[], object]) -> float:
    tree = build()

    async def go() -> float:
        start = time.perf_counter()
        await nu.arun(tree)
        return time.perf_counter() - start

    return asyncio.run(go())


def _median(runs: int, timer: Callable[[Callable[[], object]], float], build: Callable) -> float:
    timer(build)  # warm up: compile caches, imports
    return statistics.median(timer(build) for _ in range(runs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=5, help="runs per case, median reported")
    args = parser.parse_args()

    rows: list[tuple[str, str, str]] = []

    def per_item(name: str, n: int, timer: Callable, build: Callable) -> None:
        total = _median(args.runs, timer, build)
        rows.append((name, f"{total * 1e3:9.1f} ms", f"{total / n * 1e6:7.2f} us/item"))

    per_item(f"Map {N_ITEMS // 1000}k", N_ITEMS, _time_sync, map_tree)
    per_item(f"ForEachDo {N_ITEMS // 1000}k", N_ITEMS, _time_sync, foreach_tree)
    per_item(f"Filter {N_ITEMS // 1000}k", N_ITEMS, _time_sync, filter_tree)
    per_item(f"Accumulate {N_ITEMS // 1000}k", N_ITEMS, _time_sync, accumulate_tree)
    per_item(f"Reduce {N_ITEMS // 1000}k", N_ITEMS, _time_sync, reduce_tree)
    per_item(f"ForEachParAsync {N_ARMS // 1000}k arms", N_ARMS, _time_async, foreach_par_tree)

    loops = {d: _median(args.runs, _time_sync, lambda d=d: loop_tree(d)) for d in (0, DEPTH)}
    for label, build in (("mem read", mem_read_tree), ("fabric read", fabric_read_tree)):
        for depth in (0, DEPTH):
            total = _median(args.runs, _time_sync, lambda d=depth, b=build: b(d))
            net = (total - loops[depth]) / N_READS
            rows.append(
                (
                    f"{label}, {depth} Provides",
                    f"{total * 1e3:9.1f} ms",
                    f"{net * 1e9:7.0f} ns/read",
                )
            )

    print(f"context benchmark, median of {args.runs} runs")
    print(f"(read rows: {N_READS // 1000}k reads in a loop, loop overhead subtracted)")
    width = max(len(r[0]) for r in rows)
    for name, total, unit in rows:
        print(f"{name:<{width}}  {total}  {unit}")


if __name__ == "__main__":
    main()
