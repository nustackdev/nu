"""Unit tests for ``nu2.lang.runtime.runtime``.

Covers ``Runtime`` -- the concrete Runtime that drives compiled Programs.
Dispatch (``eval`` / ``aeval``), sequential and parallel helpers, stream
pumps, sentinel propagation, hybrid async pump, and the
boundary helpers (``in_thread`` / ``a_in_thread``).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from nu2.core import AddQuery, AndQuery, LiteralQuery, MulQuery, SubQuery
from nu2.lang import compile
from nu2.lang.attributes import Attr
from nu2.lang.runtime import Budget, Context, Runtime
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable


# --- helpers ---------------------------------------------------------------


def _fake_program(
    thunks: list[Callable] | None = None,
    athunks: list[Callable] | None = None,
    on_loop: list[bool] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        thunks=thunks or [],
        athunks=athunks or [],
        attrs={Attr.ON_LOOP: on_loop or []},
    )


# --- construction ----------------------------------------------------------


def test_construction_binds_program_ctx_and_budget() -> None:
    program = compile(LiteralQuery(1))
    ctx = Context()
    budget = Budget()
    rt = Runtime(program, ctx, budget=budget)
    assert rt.program is program
    assert rt.ctx is ctx
    assert rt.budget is budget


def test_construction_default_budget_is_sequential() -> None:
    program = compile(LiteralQuery(1))
    rt = Runtime(program, Context())
    assert isinstance(rt.budget, Budget)
    assert rt.budget.max_parallel == 1


# --- dispatch: eval --------------------------------------------------------


def test_eval_returns_leaf_value() -> None:
    program = compile(LiteralQuery(5))
    with Budget() as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval() == 5


def test_eval_recurses_on_arithmetic() -> None:
    program = compile(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    with Budget() as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval() == 3


def test_eval_nested_arithmetic() -> None:
    program = compile(
        AddQuery(
            MulQuery(LiteralQuery(2), LiteralQuery(3)), SubQuery(LiteralQuery(10), LiteralQuery(4))
        )
    )
    with Budget() as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval() == 12


# --- dispatch: aeval -------------------------------------------------------


async def test_aeval_returns_leaf_value() -> None:
    program = compile(LiteralQuery(7))
    with Budget(async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval() == 7


async def test_aeval_recurses_on_arithmetic() -> None:
    program = compile(MulQuery(LiteralQuery(3), LiteralQuery(4)))
    with Budget(async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval() == 12


async def test_aeval_matches_eval() -> None:
    program = compile(AndQuery(LiteralQuery(True), LiteralQuery(True)))
    with Budget(async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval() is True


# --- sentinel propagation through real atoms ------------------------------


def test_empty_operand_collapses_to_invalid() -> None:
    program = compile(AddQuery(LiteralQuery(EMPTY), LiteralQuery(1)))
    with Budget() as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval() is INVALID


def test_invalid_operand_collapses_to_invalid() -> None:
    program = compile(MulQuery(LiteralQuery(2), LiteralQuery(INVALID)))
    with Budget() as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval() is INVALID


# --- eval_or_short / aeval_or_short ---------------------------------------


def test_eval_or_short_returns_values_when_all_present() -> None:
    program = _fake_program(thunks=[lambda rt: 1, lambda rt: 2, lambda rt: 3])
    rt = Runtime(program, Context())
    assert rt.eval_or_short([0, 1, 2]) == [1, 2, 3]


def test_eval_or_short_returns_invalid_on_empty() -> None:
    program = _fake_program(thunks=[lambda rt: 1, lambda rt: EMPTY, lambda rt: 3])
    rt = Runtime(program, Context())
    assert rt.eval_or_short([0, 1, 2]) is INVALID


def test_eval_or_short_returns_invalid_on_invalid() -> None:
    program = _fake_program(thunks=[lambda rt: INVALID, lambda rt: 2])
    rt = Runtime(program, Context())
    assert rt.eval_or_short([0, 1]) is INVALID


async def test_aeval_or_short_returns_values_when_all_present() -> None:
    async def t0(rt: Runtime) -> object:
        return 10

    async def t1(rt: Runtime) -> object:
        return 20

    program = _fake_program(athunks=[t0, t1])
    rt = Runtime(program, Context())
    assert await rt.aeval_or_short([0, 1]) == [10, 20]


async def test_aeval_or_short_short_circuits_on_sentinel() -> None:
    async def t0(rt: Runtime) -> object:
        return 1

    async def t1(rt: Runtime) -> object:
        return EMPTY

    program = _fake_program(athunks=[t0, t1])
    rt = Runtime(program, Context())
    assert await rt.aeval_or_short([0, 1]) is INVALID


# --- sequential helpers ----------------------------------------------------


def test_eval_each_returns_values_in_order() -> None:
    program = _fake_program(thunks=[lambda rt: 1, lambda rt: 2, lambda rt: 3])
    rt = Runtime(program, Context())
    assert rt.eval_each([2, 0, 1]) == [3, 1, 2]


async def test_aeval_each_returns_values_in_order() -> None:
    async def mk(v: int) -> Callable:
        async def t(rt: Runtime) -> object:
            return v

        return t

    program = _fake_program(athunks=[await mk(1), await mk(2), await mk(3)])
    rt = Runtime(program, Context())
    assert await rt.aeval_each([0, 2]) == [1, 3]


# --- parallel helpers ------------------------------------------------------


def test_eval_parallel_falls_through_to_sequential_at_max_parallel_one() -> None:
    program = _fake_program(thunks=[lambda rt: 10, lambda rt: 20])
    rt = Runtime(program, Context())
    assert rt.eval_parallel([0, 1]) == [10, 20]


def test_eval_parallel_preserves_order_under_threads() -> None:
    program = _fake_program(thunks=[(lambda v: lambda rt: v)(i) for i in range(5)])
    with Budget(max_parallel=3) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert rt.eval_parallel([0, 1, 2, 3, 4]) == [0, 1, 2, 3, 4]


async def test_aeval_parallel_returns_values_in_order() -> None:
    async def mk(v: int) -> Callable:
        async def t(rt: Runtime) -> object:
            return v

        return t

    athunks = [await mk(i) for i in range(4)]
    program = _fake_program(athunks=athunks, on_loop=[True, True, True, True])
    with Budget(max_parallel=2, async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval_parallel([0, 1, 2, 3]) == [0, 1, 2, 3]


async def test_aeval_parallel_hybrid_places_sync_child_on_thread() -> None:
    # Mixed subtree: child 0 is async-on-loop, child 1 is sync-only. The hybrid
    # placement drives the async child via aeval and the sync child via the
    # thread pool, joining both - rather than running the sync one on the loop.
    async def a0(rt: Runtime) -> object:
        return 100

    def s1(rt: Runtime) -> object:
        return 200

    program = _fake_program(thunks=[None, s1], athunks=[a0, None], on_loop=[True, False])
    with Budget(max_parallel=2, async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval_parallel([0, 1]) == [100, 200]


async def test_aeval_race_returns_first_completed() -> None:
    import asyncio

    async def slow(rt: Runtime) -> object:
        await asyncio.sleep(0.1)
        return "slow"

    async def fast(rt: Runtime) -> object:
        return "fast"

    program = _fake_program(athunks=[slow, fast])
    rt = Runtime(program, Context())
    assert await rt.aeval_race([0, 1]) == "fast"


async def test_aeval_race_rejects_empty() -> None:
    program = _fake_program()
    rt = Runtime(program, Context())
    with pytest.raises(ValueError, match="aeval_race needs"):
        await rt.aeval_race([])


async def test_aeval_any_returns_first_success() -> None:
    import asyncio

    async def slow_ok(rt: Runtime) -> object:
        await asyncio.sleep(0.1)
        return "slow"

    async def fast_ok(rt: Runtime) -> object:
        return "fast"

    program = _fake_program(athunks=[slow_ok, fast_ok])
    rt = Runtime(program, Context())
    assert await rt.aeval_any([0, 1]) == "fast"


async def test_aeval_any_skips_a_failing_child() -> None:
    import asyncio

    async def boom(rt: Runtime) -> object:
        raise ValueError("nope")

    async def ok(rt: Runtime) -> object:
        await asyncio.sleep(0.05)
        return "ok"

    program = _fake_program(athunks=[boom, ok])
    rt = Runtime(program, Context())
    assert await rt.aeval_any([0, 1]) == "ok"


async def test_aeval_any_reraises_when_all_fail() -> None:
    async def boom1(rt: Runtime) -> object:
        raise ValueError("first")

    async def boom2(rt: Runtime) -> object:
        raise ValueError("second")

    program = _fake_program(athunks=[boom1, boom2])
    rt = Runtime(program, Context())
    with pytest.raises(ValueError, match=r"first|second"):
        await rt.aeval_any([0, 1])


async def test_aeval_any_rejects_empty() -> None:
    program = _fake_program()
    rt = Runtime(program, Context())
    with pytest.raises(ValueError, match="aeval_any needs"):
        await rt.aeval_any([])


# --- sentinel-propagating parallel ----------------------------------------


def test_eval_parallel_or_short_returns_invalid_on_sentinel() -> None:
    program = _fake_program(thunks=[lambda rt: 1, lambda rt: EMPTY])
    rt = Runtime(program, Context())
    assert rt.eval_parallel_or_short([0, 1]) is INVALID


def test_eval_parallel_or_short_returns_values_when_clean() -> None:
    program = _fake_program(thunks=[lambda rt: 1, lambda rt: 2])
    rt = Runtime(program, Context())
    assert rt.eval_parallel_or_short([0, 1]) == [1, 2]


async def test_aeval_parallel_or_short_returns_invalid_on_sentinel() -> None:
    async def t0(rt: Runtime) -> object:
        return 1

    async def t1(rt: Runtime) -> object:
        return INVALID

    program = _fake_program(athunks=[t0, t1])
    with Budget(async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.aeval_parallel_or_short([0, 1]) is INVALID


# --- streams: iter / collect / merge --------------------------------------


def test_iter_returns_empty_tuple_for_none() -> None:
    program = _fake_program(thunks=[lambda rt: None])
    rt = Runtime(program, Context())
    assert list(rt.iter(0)) == []


def test_iter_returns_value_when_iterable() -> None:
    program = _fake_program(thunks=[lambda rt: iter([1, 2, 3])])
    rt = Runtime(program, Context())
    assert list(rt.iter(0)) == [1, 2, 3]


def test_collect_materializes_stream_to_list() -> None:
    def gen(rt: Runtime) -> object:
        return (x for x in [4, 5, 6])

    program = _fake_program(thunks=[gen])
    rt = Runtime(program, Context())
    assert rt.collect(0) == [4, 5, 6]


async def test_acollect_materializes_async_stream() -> None:
    async def agen():
        for v in [1, 2, 3]:
            yield v

    async def athunk(rt: Runtime) -> object:
        return agen()

    program = _fake_program(athunks=[athunk])
    rt = Runtime(program, Context())
    assert await rt.acollect(0) == [1, 2, 3]


def test_merge_falls_through_at_max_parallel_one() -> None:
    def g0(rt: Runtime) -> object:
        return iter([1, 2])

    def g1(rt: Runtime) -> object:
        return iter([3, 4])

    program = _fake_program(thunks=[g0, g1])
    rt = Runtime(program, Context())
    assert sorted(rt.merge([0, 1])) == [1, 2, 3, 4]


def test_merge_yields_all_under_threads() -> None:
    def g0(rt: Runtime) -> object:
        return iter([1, 2])

    def g1(rt: Runtime) -> object:
        return iter([3, 4])

    program = _fake_program(thunks=[g0, g1])
    with Budget(max_parallel=2) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert sorted(rt.merge([0, 1])) == [1, 2, 3, 4]


# --- boundary helpers -----------------------------------------------------


def test_in_thread_returns_a_future_with_the_result() -> None:
    program = _fake_program()
    with Budget(max_parallel=2) as budget:
        rt = Runtime(program, Context(), budget=budget)
        fut = rt.in_thread(lambda x: x + 1, 41)
        assert fut.result() == 42


def test_in_thread_requires_pool() -> None:
    program = _fake_program()
    rt = Runtime(program, Context())
    with pytest.raises(RuntimeError, match="max_parallel > 1"):
        rt.in_thread(lambda: 1)


async def test_a_in_thread_awaits_blocking_call() -> None:
    program = _fake_program()
    with Budget(max_parallel=2, async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.a_in_thread(lambda x, y: x + y, 2, 3) == 5


async def test_a_in_thread_supports_kwargs() -> None:
    program = _fake_program()
    with Budget(max_parallel=2, async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        assert await rt.a_in_thread(lambda x, y: x * y, 3, y=4) == 12


async def test_a_in_thread_requires_pool() -> None:
    program = _fake_program()
    rt = Runtime(program, Context())
    with pytest.raises(RuntimeError, match="max_parallel > 1"):
        await rt.a_in_thread(lambda: 1)


# --- parallel streams: amerge (placement-aware) ---------------------------


async def test_amerge_sequential_dispatches_per_on_loop() -> None:
    async def aon():
        for v in [1, 2]:
            yield v

    def syn(rt: Runtime) -> object:
        return iter([3, 4])

    async def t_on(rt: Runtime) -> object:
        return aon()

    async def t_off(rt: Runtime) -> object:  # pragma: no cover - not reached
        return None

    program = _fake_program(
        thunks=[None, syn],
        athunks=[t_on, t_off],
        on_loop=[True, False],
    )
    rt = Runtime(program, Context())
    got = [v async for v in rt.amerge([0, 1])]
    assert sorted(got) == [1, 2, 3, 4]


async def test_amerge_parallel_yields_all() -> None:
    async def aon():
        for v in [1, 2]:
            yield v

    def syn(rt: Runtime) -> object:
        return iter([3, 4])

    async def t_on(rt: Runtime) -> object:
        return aon()

    async def t_off(rt: Runtime) -> object:  # pragma: no cover - not reached
        return None

    program = _fake_program(
        thunks=[None, syn],
        athunks=[t_on, t_off],
        on_loop=[True, False],
    )
    with Budget(max_parallel=2, async_mode=True) as budget:
        rt = Runtime(program, Context(), budget=budget)
        got = [v async for v in rt.amerge([0, 1])]
        assert sorted(got) == [1, 2, 3, 4]


async def test_amerge_rejects_non_async_budget() -> None:
    program = _fake_program(thunks=[lambda rt: iter([])], athunks=[None], on_loop=[False])
    with Budget(max_parallel=2, async_mode=False) as budget:
        rt = Runtime(program, Context(), budget=budget)
        with pytest.raises(RuntimeError, match="amerge requires"):
            async for _ in rt.amerge([0]):  # pragma: no cover - generator body
                pass


# --- context interaction --------------------------------------------------


def test_ctx_attrs_writes_are_visible_through_runtime() -> None:
    program = compile(LiteralQuery(1))
    ctx = Context()
    ctx.attrs["x"] = 42
    with Budget() as budget:
        rt = Runtime(program, ctx, budget=budget)
        assert rt.ctx.attrs["x"] == 42
        rt.ctx.attrs["y"] = "hello"
    assert ctx.attrs["y"] == "hello"


# --- budget lifecycle -----------------------------------------------------


def test_budget_close_after_runtime_drive() -> None:
    program = compile(LiteralQuery(1))
    budget = Budget(max_parallel=2)
    rt = Runtime(program, Context(), budget=budget)
    assert rt.eval() == 1
    assert budget.thread_pool is not None
    budget.close()
    assert budget.thread_pool is None
