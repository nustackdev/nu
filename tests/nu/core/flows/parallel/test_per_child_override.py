"""Per-child mode override via ``(child, "threaded"|"async")`` tuples on Parallel.

Placement precedence on ``Parallel``:

1. class-level ``_FORCE_MODE`` (``ParallelThreaded`` / ``ParallelAsync``) -
   not exercised here; see ``test_forced_mode_parallel``.
2. per-child override from the tuple.
3. ``Attr.ON_LOOP`` (smart choice) - the fallback.

Here we pin (2) beats (3): a runs-anywhere child forced ``"threaded"`` lands
on a worker; forced ``"async"`` lands on the loop.
"""

from __future__ import annotations

import threading

from _support.async_atoms import RunsAnywhereAction

from nu.core.flows import Parallel
from nu.lang.helpers import arun


def _this_thread() -> str:
    return threading.current_thread().name


def _is_worker(name: str) -> bool:
    return name.startswith("nu-worker")


async def test_parallel_per_child_threaded_overrides_smart_choice() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        Parallel((RunsAnywhereAction("t"), "threaded"), (RunsAnywhereAction("a"), "async")),
        max_parallel=2,
    )
    assert _is_worker(ctx.attrs["t"])
    assert ctx.attrs["a"] == loop


async def test_parallel_mixed_tuple_and_bare_children() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        Parallel(RunsAnywhereAction("bare"), (RunsAnywhereAction("t"), "threaded")),
        max_parallel=2,
    )
    # bare child follows the smart choice; the forced-threaded child lands
    # on a worker regardless.
    assert _is_worker(ctx.attrs["t"])
    assert ctx.attrs["bare"] == loop or _is_worker(ctx.attrs["bare"])
