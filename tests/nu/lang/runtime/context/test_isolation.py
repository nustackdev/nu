"""Context isolation at every point a task starts.

Each concurrent task runs on its own ``Context.branch()``: Parallel / Race /
AnyN arms (on the loop, on a thread, or in the sequential fallback),
ForEachPar arms, ReactLatest runs, and worker requests. For both stores the
rules are the same:

- an arm sees what the parent had bound before the arm started;
- siblings never see each other's ``let`` / ``set`` / ``bind``;
- the parent never sees an arm's, whether the arm finishes, raises, or is
  cancelled.

Arms here are built from ``_Fn``, an atom running a Python function against
its ``rt``, so a test can hold a scope open across an ``await`` and order two
arms with events.
"""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import threading
from typing import TYPE_CHECKING

import pytest

import nu
from nu.context import Attr, FabricRef, Provide
from nu.core.flows import AnyN, ForEachParAsync, Parallel, ParallelThreaded, Race, ReactLatest
from nu.engine.structure import Declared
from nu.lang import Context, ScalarAction
from nu.lang.helpers import arun, run


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


class Handle:
    """A fabric an arm provides and a sibling looks for."""


class Parent:
    """A fabric the parent provides before any arm starts."""


class _SyncFn(ScalarAction):
    """Runs a plain ``fn(rt)`` on either path, so it may land on a thread."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._payload["fn"]

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return fn(rt)

        return athunk


class _AsyncFn(_SyncFn):
    """Awaits a coroutine ``fn(rt)``; async-only, so it always runs on the loop."""

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_AsyncFn was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._payload["fn"]


def _Fn(fn: Callable) -> ScalarAction:  # noqa: N802 (reads as the atom it builds)
    """The arm atom for ``fn``: ``_AsyncFn`` for a coroutine function, else ``_SyncFn``."""
    return _AsyncFn(fn) if inspect.iscoroutinefunction(fn) else _SyncFn(fn)


def _view(rt: Runtime) -> dict:
    """What an arm can see: its names, and which fabrics resolve."""
    ctx = rt.ctx
    return {
        "attrs": dict(ctx.attrs.items()),
        "handle": ctx.fabrics.has(Handle),
        "parent": ctx.fabrics.has(Parent),
    }


def _start_ctx() -> Context:
    """The parent: one name declared and one fabric provided before any arm."""
    return Context(attrs={"x": 0, "p": "parent"}).bind(Parent, Parent())


def _assert_parent_untouched(ctx: Context) -> None:
    assert dict(ctx.attrs.items()) == {"x": 0, "p": "parent"}
    assert ctx.fabrics.has(Handle) is False


# --- Nu-level regressions ---------------------------------------------------
# Each arm opens a binder's scope on the same name; one arm leaving its scope
# must never take the name away from its sibling or hand it to the parent.

x = nu.Attr("x")


def _binding(value: object, body: nu.Nu) -> nu.Nu:
    """``body`` run with ``value`` bound under ``x`` by a real binder."""
    return nu.ForEachDo(nu.Iter([value]), body, item="x")


def test_parallel_sibling_binding_outlives_the_other_arm_sync(
    capsys: pytest.CaptureFixture,
) -> None:
    run(
        nu.Parallel(
            _binding(1, nu.Delay(0.01)), _binding(2, nu.Delay(0.05) >> nu.print(x.exists()))
        )
    )
    assert capsys.readouterr().out == "True\n"


@pytest.mark.parametrize("max_parallel", [1, 2])
async def test_parallel_sibling_binding_outlives_the_other_arm_async(
    max_parallel: int, capsys: pytest.CaptureFixture
) -> None:
    tree = nu.Parallel(_binding(1, nu.Delay(0.01)), _binding(2, nu.Delay(0.05) >> nu.print(x)))
    await arun(tree, max_parallel=max_parallel)
    assert capsys.readouterr().out == "2\n"


async def test_anyn_sibling_binding_outlives_a_failed_arm(capsys: pytest.CaptureFixture) -> None:
    failing = _binding(1, nu.Delay(0.01) >> nu.print(nu.Div(1, 0)))
    await arun(AnyN(failing, _binding(2, nu.Delay(0.05) >> nu.print(x))))
    assert capsys.readouterr().out == "2\n"


async def test_race_sibling_binding_outlives_a_cancelled_arm(
    capsys: pytest.CaptureFixture,
) -> None:
    # The Delay arm wins, the binding arm is cancelled mid-scope; its
    # unwinding must not reach the parent, which never bound x.
    await arun(Race(nu.Delay(0.01), _binding(2, nu.Delay(1.0))) >> nu.print(x.exists()))
    assert capsys.readouterr().out == "False\n"


# --- two arms, one holding its scopes open while the other looks -------------


def _async_pair(seen: dict) -> tuple[ScalarAction, ScalarAction]:
    """Arm ``a`` binds everything and waits; arm ``b`` looks, then lets ``a`` go."""
    a_bound, b_looked = asyncio.Event(), asyncio.Event()

    async def a(rt: Runtime) -> str:
        seen["a_start"] = _view(rt)
        with rt.ctx.attrs.let("mine", "a"), rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", "a")
            a_bound.set()
            await b_looked.wait()
            seen["a_inside"] = _view(rt)
        return "a"

    async def b(rt: Runtime) -> str:
        await a_bound.wait()
        seen["b"] = _view(rt)
        b_looked.set()
        return "b"

    return _Fn(a), _Fn(b)


@pytest.mark.parametrize("flow", [Parallel, Race, AnyN])
@pytest.mark.parametrize("max_parallel", [1, 2])
async def test_arms_are_isolated_on_the_loop(flow: type, max_parallel: int) -> None:
    seen: dict = {}
    _, ctx = await arun(flow(*_async_pair(seen)), _start_ctx(), max_parallel=max_parallel)

    # the arm saw the parent's bindings from before it started
    assert seen["a_start"] == {"attrs": {"x": 0, "p": "parent"}, "handle": False, "parent": True}
    # the sibling never saw a's let / set / bind
    assert seen["b"] == {"attrs": {"x": 0, "p": "parent"}, "handle": False, "parent": True}
    _assert_parent_untouched(ctx)


async def test_parallel_arms_are_isolated_under_a_parent_scope() -> None:
    # The parent's own scopes (a binder and a Provide around the fan-out)
    # reach the arms; nothing an arm opens reaches back.
    seen: dict = {}
    tree = nu.ForEachDo(
        nu.Iter(["scoped"]),
        Provide(
            Handle, {}, Parallel(*_async_pair(seen)) >> _Fn(lambda rt: seen.update(after=_view(rt)))
        ),
        item="q",
    )
    _, ctx = await arun(tree, _start_ctx())
    assert seen["b"]["attrs"] == {"x": 0, "p": "parent", "q": "scoped"}
    assert seen["b"]["handle"] is True  # the parent's Handle, not a's
    assert seen["after"]["attrs"] == {"x": 0, "p": "parent", "q": "scoped"}
    _assert_parent_untouched(ctx)


# --- sync Parallel: sequential fallback and threads -------------------------


def _sync_pair(seen: dict, *, overlap: bool) -> tuple[ScalarAction, ScalarAction]:
    """Sync arms; with ``overlap`` they run on two threads and wait on each other."""
    a_bound, b_looked = threading.Event(), threading.Event()

    def a(rt: Runtime) -> str:
        seen["a_start"] = _view(rt)
        with rt.ctx.attrs.let("mine", "a"), rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", "a")
            if overlap:
                a_bound.set()
                assert b_looked.wait(2)
        return "a"

    def b(rt: Runtime) -> str:
        if overlap:
            assert a_bound.wait(2)
        seen["b"] = _view(rt)
        b_looked.set()
        return "b"

    return _Fn(a), _Fn(b)


def test_sync_parallel_sequential_arms_are_isolated() -> None:
    seen: dict = {}
    _, ctx = run(Parallel(*_sync_pair(seen, overlap=False)), _start_ctx())
    assert seen["b"] == {"attrs": {"x": 0, "p": "parent"}, "handle": False, "parent": True}
    _assert_parent_untouched(ctx)


def test_sync_parallel_threaded_arms_are_isolated() -> None:
    seen: dict = {}
    _, ctx = run(Parallel(*_sync_pair(seen, overlap=True)), _start_ctx(), max_parallel=2)
    assert seen["a_start"]["parent"] is True
    assert seen["b"] == {"attrs": {"x": 0, "p": "parent"}, "handle": False, "parent": True}
    _assert_parent_untouched(ctx)


# --- thread handoff under the async runtime ---------------------------------

_TRACE: contextvars.ContextVar[str] = contextvars.ContextVar("trace")


async def test_thread_arm_keeps_its_task_context() -> None:
    seen: dict = {}
    _TRACE.set("from-the-loop")

    def arm(rt: Runtime) -> None:
        seen["thread"] = threading.current_thread().name
        seen["view"] = _view(rt)
        seen["trace"] = _TRACE.get(None)
        with rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", "thread")

    _, ctx = await arun(
        ParallelThreaded(_Fn(arm), _Fn(lambda rt: None)), _start_ctx(), max_parallel=2
    )
    assert seen["thread"].startswith("nu-worker")
    assert seen["view"] == {"attrs": {"x": 0, "p": "parent"}, "handle": False, "parent": True}
    assert seen["trace"] == "from-the-loop"  # Python contextvars ride along too
    _assert_parent_untouched(ctx)


# --- error and cancellation --------------------------------------------------


@pytest.mark.parametrize("max_parallel", [1, 2])
async def test_a_failing_arm_leaves_parent_and_sibling_alone(max_parallel: int) -> None:
    seen: dict = {}
    a_bound = asyncio.Event()

    async def a(rt: Runtime) -> None:
        with rt.ctx.attrs.let("mine", "a"), rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", "a")
            a_bound.set()
            await asyncio.sleep(0)
            raise ValueError("boom")

    async def b(rt: Runtime) -> None:
        await a_bound.wait()
        seen["b"] = _view(rt)

    ctx = _start_ctx()
    with pytest.raises(ValueError, match="boom"):
        await arun(Parallel(_Fn(a), _Fn(b)), ctx, max_parallel=max_parallel)
    assert seen["b"]["attrs"] == {"x": 0, "p": "parent"}
    assert seen["b"]["handle"] is False
    _assert_parent_untouched(ctx)


@pytest.mark.parametrize("flow", [Race, AnyN])
async def test_a_cancelled_arm_unwinds_its_own_scopes(flow: type) -> None:
    arm_ctx: list[Context] = []
    bound = asyncio.Event()

    async def held(rt: Runtime) -> None:
        arm_ctx.append(rt.ctx)
        with rt.ctx.attrs.let("mine", "held"), rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", "held")
            bound.set()
            await asyncio.Event().wait()

    async def winner(rt: Runtime) -> str:
        await bound.wait()
        return "won"

    _, ctx = await arun(flow(_Fn(held), _Fn(winner)), _start_ctx())
    (branch,) = arm_ctx
    assert branch is not ctx
    assert branch.attrs.exists("mine") is False  # let unwound on cancel
    assert branch.fabrics.has(Handle) is False  # bind unwound on cancel
    assert branch.attrs.get("x") == "held"  # the set stayed on the branch
    _assert_parent_untouched(ctx)


# --- ForEachPar ------------------------------------------------------------


async def test_foreach_par_arms_are_isolated() -> None:
    seen: dict = {}
    one_bound, two_looked = asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        item = rt.ctx.attrs.get("item")
        if item == 1:
            with rt.ctx.attrs.let("mine", 1), rt.ctx.fabrics.bind(Handle, Handle()):
                rt.ctx.attrs.set("x", 1)
                one_bound.set()
                await two_looked.wait()
        else:
            await one_bound.wait()
            seen[item] = _view(rt)
            two_looked.set()

    _, ctx = await arun(ForEachParAsync(nu.Iter(nu.Literal([1, 2])), _Fn(body)), _start_ctx())
    assert seen[2] == {"attrs": {"x": 0, "p": "parent", "item": 2}, "handle": False, "parent": True}
    _assert_parent_untouched(ctx)


# --- ReactLatest runs --------------------------------------------------------


class _Feed:
    """A Subscription the test fires by hand."""

    def __init__(self) -> None:
        self.receivers: list = []

    def bind(self, receiver: Callable) -> None:
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.receivers.remove(receiver)

    def close(self) -> None:
        pass

    def fire(self, key: object) -> None:
        for receiver in list(self.receivers):
            receiver(key)


async def _until(check: Callable[[], bool]) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), 2.0)


async def test_react_latest_runs_are_isolated() -> None:
    feed, seen = _Feed(), {}

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        seen[key] = _view(rt)
        with rt.ctx.attrs.let("mine", key), rt.ctx.fabrics.bind(Handle, Handle()):
            rt.ctx.attrs.set("x", key)
            await asyncio.Event().wait()

    ctx = Context(attrs={"x": 0, "p": "parent", "feed": feed}).bind(Parent, Parent())
    term = ReactLatest(Attr("feed"), _Fn(body), changed_key="k")
    task = asyncio.ensure_future(arun(term, ctx))
    await _until(lambda: feed.receivers)
    for key in ("a", "b"):
        feed.fire(key)
        await _until(lambda key=key: key in seen)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # run b started after run a had set x and bound a Handle, and saw neither
    assert seen["b"] == {
        "attrs": {"x": 0, "p": "parent", "feed": feed, "k": "b"},
        "handle": False,
        "parent": True,
    }
    assert dict(ctx.attrs.items()) == {"x": 0, "p": "parent", "feed": feed}
    assert ctx.fabrics.has(Handle) is False


# --- worker handoff -----------------------------------------------------------


def _worker_exec_contexts() -> list[Callable]:
    from nustd.mp._worker import _exec_context as mp_exec
    from nustd.mp_pool._worker import _exec_context as pool_exec

    return [mp_exec, pool_exec]


@pytest.mark.parametrize("exec_context", _worker_exec_contexts())
def test_worker_request_seeds_names_on_its_own_branch(exec_context: Callable) -> None:
    worker = Context()
    with worker.fabrics.bind(Parent, Parent()):
        with exec_context(worker, {"x": 1}) as one, exec_context(worker, {"x": 2}) as two:
            assert one.attrs.get("x") == 1
            assert two.attrs.get("x") == 2
            assert one.fabrics.has(Parent) is True  # the worker's own fabrics
            one.attrs.set("x", 10)
            with one.fabrics.bind(Handle, Handle()):
                assert two.fabrics.has(Handle) is False
            assert two.attrs.get("x") == 2
        assert worker.attrs.exists("x") is False
        assert worker.fabrics.has(Handle) is False


@pytest.mark.parametrize("exec_context", _worker_exec_contexts())
def test_worker_request_without_names_still_gets_a_branch(exec_context: Callable) -> None:
    worker = Context()
    with exec_context(worker, None) as ctx:
        assert ctx is not worker
        assert dict(ctx.attrs.items()) == {}


def test_worker_handoff_runs_a_tree_against_the_seeded_names() -> None:
    from nustd.mp._worker import _exec_context

    with _exec_context(Context(), {"x": 41}) as ctx:
        value, _ = run(x + 1, ctx)
    assert value == 42


# --- brackets under a fan-out -------------------------------------------------


@pytest.mark.parametrize("max_parallel", [1, 2])
async def test_a_bracket_fabric_is_not_seen_by_a_sibling_arm(
    max_parallel: int, capsys: pytest.CaptureFixture
) -> None:
    handle = FabricRef(Handle)
    tree = Parallel(
        Provide(Handle, {}, nu.print(handle.exists()) >> nu.Delay(0.05)),
        nu.Delay(0.01) >> nu.print(handle.exists()),
    )
    await arun(tree >> nu.print(handle.exists()), max_parallel=max_parallel)
    assert capsys.readouterr().out.split() == ["True", "False", "False"]
