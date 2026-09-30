"""Tree-level tests for the ``nustd.mp_pool`` atoms. Real processes, no mocks.

Two drive styles are used on purpose:

- ``Provide(WorkerPool, ...)`` around the tree, for the bracket wiring.
- a ``WorkerPool`` the test builds and binds on the Context itself, for the
  cases that need to assert on the pool *after* the tree finished. A
  ``Provide`` tears its fabric down on the way out, so there would be nothing
  left to look at.
"""

from __future__ import annotations

import os
import time

import pytest
from _support.pool_workers import RESIDENT

import nu
import nustd
from nustd.mp_pool import Alive, Dispatch, Kill, Launch, Running, Teleport, WorkerPool, Workers


pytestmark = pytest.mark.slow


class Local(nu.Shape):
    """The worker a tree launched, held for the rest of the tree."""

    w = nustd.mem.IntRef.slot()


W = Local.w


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test-tree")
    p.setup(None)
    try:
        yield p
    finally:
        p.cleanup()


@pytest.fixture
def ctx(pool):
    return nu.Context().bind(WorkerPool, pool)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _await_true(fn, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        time.sleep(0.01)
    return False


# --- the bracket ------------------------------------------------------------


def test_provide_launch_teleport_round_trip():
    tree = nu.Provide(
        WorkerPool,
        {"name": "nu-test-provide"},
        nustd.mem.Frame(Local, Teleport(body=nu.Add(41, 1), worker=W), w=Launch()),
    )
    value, _ = nu.run(tree)
    assert value == 42


async def test_provide_launch_teleport_round_trip_async():
    tree = nu.Provide(
        WorkerPool,
        {"name": "nu-test-provide-a"},
        nustd.mem.Frame(Local, Teleport(body=nu.Add(41, 1), worker=W), w=Launch()),
    )
    value, _ = await nu.arun(tree)
    assert value == 42


def test_provide_teardown_kills_the_worker_it_launched():
    seen: list[int] = []

    class _Spy(WorkerPool):
        def launch(self, init=None):
            wid = super().launch(init)
            seen.append(self._workers[wid].proc.pid)
            return wid

    tree = nu.Provide(
        _Spy,
        {"name": "nu-test-teardown-tree"},
        nustd.mem.Frame(Local, Teleport(body=nu.Add(1, 1), worker=W), w=Launch()),
        bind_as=WorkerPool,
    )
    value, _ = nu.run(tree)
    assert value == 2
    assert seen
    assert not _pid_alive(seen[0])


# --- the no-payload requirement ---------------------------------------------


def test_worker_id_flows_from_a_ref(ctx, pool):
    """The id reaches Teleport through a mem slot, i.e. it is a child, not payload."""
    tree = nustd.mem.Frame(Local, Teleport(body=nu.Add(1, 2), worker=W), w=Launch())
    value, _ = nu.run(tree, ctx)
    assert value == 3


def test_worker_id_flows_from_a_computed_query(ctx, pool):
    """And through a query over that ref, which a payload target could never do."""
    tree = nustd.mem.Frame(
        Local,
        Teleport(body=nu.Add(1, 2), worker=nu.Add(W, 0)),
        w=Launch(),
    )
    value, _ = nu.run(tree, ctx)
    assert value == 3


def test_worker_id_flows_from_a_ref_into_dispatch_and_kill(ctx, pool):
    tree = nustd.mem.Frame(
        Local,
        Dispatch(body=RESIDENT, worker=W),
        w=Launch(),
    )
    nu.run(tree, ctx)

    wid = pool.workers()[0]
    pid = pool._workers[wid].proc.pid
    assert pool.running(wid) is True

    nu.run(nustd.mem.Frame(Local, Kill(worker=W), w=nu.Literal(wid)), ctx)
    assert pool.workers() == []
    assert not _pid_alive(pid)


def test_pool_can_be_addressed_by_an_explicit_ref():
    """``PoolRef`` is a plain FabricRef: it reads the untagged binding."""
    from nustd.mp_pool import PoolRef

    tree = nu.Provide(
        WorkerPool,
        {"name": "nu-test-ref"},
        nustd.mem.Frame(
            Local,
            Teleport(PoolRef(), body=nu.Add(2, 2), worker=W),
            w=Launch(PoolRef()),
        ),
    )
    value, _ = nu.run(tree)
    assert value == 4


# --- the fluent interface ---------------------------------------------------


def test_the_fluent_form_runs_the_same_as_the_constructors():
    from nustd.mp_pool import PoolRef

    pool = PoolRef()
    tree = nu.Provide(
        WorkerPool,
        {"name": "nu-test-fluent"},
        nustd.mem.Frame(Local, pool.teleport(nu.Add(20, 22), W), w=pool.launch()),
    )
    value, _ = nu.run(tree)
    assert value == 42


def test_the_fluent_form_drives_a_whole_lifecycle(ctx, pool):
    from nustd.mp_pool import PoolRef

    ref = PoolRef()
    nu.run(
        nustd.mem.Frame(
            Local,
            ref.dispatch(RESIDENT, W),
            w=ref.launch(),
        ),
        ctx,
    )
    wid = pool.workers()[0]
    assert nu.run(ref.alive(nu.Literal(wid)), ctx)[0] is True
    assert nu.run(ref.running(nu.Literal(wid)), ctx)[0] is True
    assert nu.run(nu.Collect(ref.workers()), ctx)[0] == [wid]

    nu.run(ref.kill(nu.Literal(wid)), ctx)
    assert nu.run(ref.alive(nu.Literal(wid)), ctx)[0] is False
    assert pool.workers() == []


# --- dispatch semantics in a tree -------------------------------------------


def test_dispatch_in_a_tree_returns_promptly(ctx, pool):
    tree = nustd.mem.Frame(
        Local,
        Dispatch(body=RESIDENT, worker=W),
        w=Launch(),
    )
    # Launch dominates the timing; the point is that it returns at all, since
    # the dispatched body never terminates.
    start = time.monotonic()
    nu.run(tree, ctx)
    assert time.monotonic() - start < 10.0
    assert pool.running(pool.workers()[0]) is True


def test_dispatch_carries_caller_attrs_when_asked(pool):
    ctx = nu.Context(attrs={"seed": 7}).bind(WorkerPool, pool)
    tree = nustd.mem.Frame(
        Local,
        Dispatch(body=nu.Attr("seed"), worker=W, carry=True),
        w=Launch(),
    )
    nu.run(tree, ctx)
    wid = pool.workers()[0]
    # The carried body reads the caller's attr on a copy of the worker Context;
    # what we assert is that it completed rather than failing.
    assert _await_true(lambda: pool.running(wid) is False)


# --- the reads --------------------------------------------------------------


def test_alive_and_running_as_tree_queries(ctx, pool):
    alive, _ = nu.run(nustd.mem.Frame(Local, Alive(worker=W), w=Launch()), ctx)
    assert alive is True
    wid = pool.workers()[0]
    running, _ = nu.run(Running(worker=nu.Literal(wid)), ctx)
    assert running is False


def test_alive_is_false_for_a_killed_id(ctx, pool):
    wid = pool.launch()
    pool.kill(wid)
    value, _ = nu.run(Alive(worker=nu.Literal(wid)), ctx)
    assert value is False


def test_workers_streams_the_ids(ctx, pool):
    a = pool.launch()
    b = pool.launch()
    value, _ = nu.run(nu.Collect(Workers()), ctx)
    assert value == [a, b]


async def test_workers_streams_the_ids_async(ctx, pool):
    a = pool.launch()
    value, _ = await nu.arun(nu.Collect(Workers()), ctx)
    assert value == [a]


def test_unbound_pool_raises_a_named_error():
    with pytest.raises(RuntimeError, match="no WorkerPool is bound"):
        nu.run(nu.Collect(Workers()))
