"""Tree-level tests for the ``nustd.mp`` atoms. Real processes, no mocks.

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
from nustd.mp import (
    Dispatch,
    Kill,
    Launch,
    PoolRef,
    Status,
    Teleport,
    WorkerPool,
    Workers,
    WorkerStatus,
)
from nustd.mp import (
    pool as pool_preset,
)


pytestmark = pytest.mark.slow


class Local(nu.Shape):
    """The worker a tree launched, held for the rest of the tree."""

    w = nu.mem.IntRef.slot()


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
        kwargs={"name": "nu-test-provide"},
        body=nu.mem.let(Local, Teleport(None, nu.Add(41, 1), W), w=Launch()),
    )
    value, _ = nu.run(tree)
    assert value == 42


async def test_provide_launch_teleport_round_trip_async():
    tree = nu.Provide(
        WorkerPool,
        kwargs={"name": "nu-test-provide-a"},
        body=nu.mem.let(Local, Teleport(None, nu.Add(41, 1), W), w=Launch()),
    )
    value, _ = await nu.arun(tree)
    assert value == 42


def test_provide_teardown_kills_the_worker_it_launched():
    seen: list[int] = []

    class _Spy(WorkerPool, nu.Fabric):
        def launch(self, init=None):
            wid = super().launch(init)
            seen.append(self._workers[wid].proc.pid)
            return wid

    tree = nu.Provide(
        _Spy,
        kwargs={"name": "nu-test-teardown-tree"},
        body=nu.mem.let(Local, Teleport(None, nu.Add(1, 1), W), w=Launch()),
        bind_as=WorkerPool,
    )
    value, _ = nu.run(tree)
    assert value == 2
    assert seen
    assert not _pid_alive(seen[0])


# --- the no-payload requirement ---------------------------------------------


def test_worker_id_flows_from_a_ref(ctx, pool):
    """The id reaches Teleport through a mem slot, i.e. it is a child, not payload."""
    tree = nu.mem.let(Local, Teleport(None, nu.Add(1, 2), W), w=Launch())
    value, _ = nu.run(tree, ctx)
    assert value == 3


def test_worker_id_flows_from_a_computed_query(ctx, pool):
    """And through a query over that ref, which a payload target could never do."""
    tree = nu.mem.let(
        Local,
        Teleport(None, nu.Add(1, 2), nu.Add(W, 0)),
        w=Launch(),
    )
    value, _ = nu.run(tree, ctx)
    assert value == 3


def test_worker_id_flows_from_a_ref_into_dispatch_and_kill(ctx, pool):
    tree = nu.mem.let(
        Local,
        Dispatch(None, RESIDENT, W),
        w=Launch(),
    )
    nu.run(tree, ctx)

    wid = pool.workers()[0]
    pid = pool.status(wid).pid
    assert pool.status(wid).state == "busy"

    nu.run(nu.mem.let(Local, Kill(worker=W), w=nu.Literal(wid)), ctx)
    assert pool.workers() == []
    assert not _pid_alive(pid)


def test_pool_can_be_addressed_by_an_explicit_ref():
    """``PoolRef()`` reads the untagged binding."""
    tree = nu.Provide(
        WorkerPool,
        kwargs={"name": "nu-test-ref"},
        body=nu.mem.let(
            Local,
            Teleport(PoolRef(), nu.Add(2, 2), W),
            w=Launch(PoolRef()),
        ),
    )
    value, _ = nu.run(tree)
    assert value == 4


# --- the fluent interface ---------------------------------------------------


def test_the_fluent_form_runs_the_same_as_the_constructors():
    pool = PoolRef()
    tree = nu.Provide(
        WorkerPool,
        kwargs={"name": "nu-test-fluent"},
        body=nu.mem.let(Local, pool.teleport(nu.Add(20, 22), W), w=pool.launch()),
    )
    value, _ = nu.run(tree)
    assert value == 42


def test_the_fluent_form_drives_a_whole_lifecycle(ctx, pool):
    ref = PoolRef()
    nu.run(
        nu.mem.let(
            Local,
            ref.dispatch(RESIDENT, W),
            w=ref.launch(),
        ),
        ctx,
    )
    wid = pool.workers()[0]
    status = nu.run(ref.status(nu.Literal(wid)), ctx)[0]
    assert (status.state, len(status.jobs)) == ("busy", 1)
    assert nu.run(nu.Collect(ref.workers()), ctx)[0] == [wid]

    nu.run(ref.kill(nu.Literal(wid)), ctx)
    status = nu.run(ref.status(nu.Literal(wid)), ctx)[0]
    assert (status.state, status.cause, status.exitcode) == ("exited", "killed", -9)
    assert pool.workers() == []


# --- dispatch semantics in a tree -------------------------------------------


def test_dispatch_in_a_tree_returns_promptly(ctx, pool):
    tree = nu.mem.let(
        Local,
        Dispatch(None, RESIDENT, W),
        w=Launch(),
    )
    # Launch dominates the timing; the point is that it returns at all, since
    # the dispatched body never terminates.
    start = time.monotonic()
    nu.run(tree, ctx)
    assert time.monotonic() - start < 10.0
    assert pool.status(pool.workers()[0]).state == "busy"


def test_dispatch_hands_its_args_to_the_body(ctx, pool):
    tree = nu.mem.let(
        Local,
        Dispatch(None, lambda seed: nu.Add(seed, 1), W, seed=7),
        w=Launch(),
    )
    nu.run(tree, ctx)
    wid = pool.workers()[0]
    # A body reading a slot with no frame on the worker would fail with a
    # LookupError, kept on the status; it completing clean means the value crossed.
    assert _await_true(lambda: pool.status(wid).jobs == ())
    assert pool.status(wid).errors == ()


# --- teleport args ----------------------------------------------------------


def test_teleport_args_are_evaluated_in_the_caller(ctx):
    tree = nu.mem.let(
        Local,
        nu.let(lambda seed: Teleport(None, lambda n: nu.Add(n, 1), W, n=seed * 2), seed=3),
        w=Launch(),
    )
    assert nu.run(tree, ctx)[0] == 7


def test_teleport_args_cross_as_values(ctx):
    body = lambda rows, meta: nu.List.of(rows, meta)  # noqa: E731
    tree = nu.mem.let(
        Local,
        Teleport(None, body, W, rows=nu.Literal(factory=lambda: [1, 2, 3]), meta={"k": "v"}),
        w=Launch(),
    )
    assert nu.run(tree, ctx)[0] == [[1, 2, 3], {"k": "v"}]


def test_a_teleported_ref_is_live_on_the_worker(ctx):
    """The generated Shapes cross with the body; its refs and a nested binding's read on the worker."""
    body = lambda n: nu.Collect(nu.Map(nu.Iter([1, 2]), lambda x: nu.Add(x, n)))  # noqa: E731
    tree = nu.mem.let(Local, Teleport(None, body, W, n=40), w=Launch())
    assert nu.run(tree, ctx)[0] == [41, 42]


async def test_teleport_args_async(ctx):
    tree = nu.mem.let(
        Local,
        nu.List.of(
            Teleport(None, lambda a, b: nu.Add(a, b), W, a=40, b=2),
            Teleport(None, nu.Add(1, 2), W),
        ),
        w=Launch(),
    )
    assert (await nu.arun(tree, ctx))[0] == [42, 3]


def test_teleport_args_per_item_of_a_loop(ctx):
    each = nu.Map(nu.Iter([1, 2, 3]), lambda x: Teleport(None, lambda y: nu.Mul(y, 10), W, y=x))
    tree = nu.mem.let(Local, nu.Collect(each), w=Launch())
    assert nu.run(tree, ctx)[0] == [10, 20, 30]


def test_config_is_positional_so_a_parameter_can_take_its_name(ctx):
    body = lambda pool, body, worker: nu.Add(pool, nu.Add(body, worker))  # noqa: E731
    tree = nu.mem.let(
        Local,
        PoolRef().teleport(body, W, pool=1, body=2, worker=3),
        w=Launch(),
    )
    assert nu.run(tree, ctx)[0] == 6


@pytest.mark.parametrize(
    ("build", "match"),
    [
        (lambda: Teleport(None, lambda a: a, 0), "no value for"),
        (lambda: Teleport(None, lambda a: a, 0, a=1, b=2), "name no parameter"),
        (lambda: Teleport(None, nu.Add(1, 2), 0, a=1), "a tree body takes no values"),
        (lambda: Dispatch(None, lambda a: a, 0, b=1), "Dispatch"),
        (lambda: PoolRef().teleport(lambda *a: a, 0), "fixed list"),
    ],
)
def test_teleport_args_are_checked_at_build(build, match):
    with pytest.raises(TypeError, match=match):
        build()


# --- the reads --------------------------------------------------------------


def test_status_as_a_tree_query(ctx, pool):
    status, _ = nu.run(nu.mem.let(Local, Status(worker=W), w=Launch()), ctx)
    assert isinstance(status, WorkerStatus)
    assert (status.state, status.jobs, status.exitcode, status.cause) == ("idle", (), None, None)
    assert status.pid == status.pgid
    assert status.name == f"nu:{pool.name}-{status.wid}"


async def test_status_as_a_tree_query_async(ctx, pool):
    wid = pool.launch()
    status, _ = await nu.arun(Status(worker=nu.Literal(wid)), ctx)
    assert status.state == "idle"


def test_status_reads_a_killed_id(ctx, pool):
    wid = pool.launch()
    pool.kill(wid)
    value, _ = nu.run(Status(worker=nu.Literal(wid)), ctx)
    assert (value.state, value.cause) == ("exited", "killed")


def test_the_preset_stands_the_pool_up_and_stops_it():
    ref = PoolRef()
    tree = pool_preset(
        name="nu-test-preset",
        grace=2.0,
        body=nu.mem.let(Local, ref.teleport(nu.Add(1, 1), W), w=ref.launch()),
    )
    assert nu.run(tree)[0] == 2


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


# --- what crosses the pipe ---------------------------------------------------


def test_a_tree_over_a_local_shape_runs_on_a_worker(ctx):
    class Tally(nu.Shape):
        n = nu.mem.IntRef.slot()

    body = nu.mem.let(Tally, nu.Add(Tally.n, 1), n=41)
    tree = nu.mem.let(Local, Teleport(None, body, W), w=Launch())
    assert nu.run(tree, ctx)[0] == 42


async def test_a_let_runs_on_a_worker(ctx):
    body = nu.mem.let(lambda n: nu.Add(n, 1), n=41)
    tree = nu.mem.let(Local, Teleport(None, body, W), w=Launch())
    assert (await nu.arun(tree, ctx))[0] == 42


def test_an_init_holding_a_local_class_reaches_the_worker(ctx):
    class Greeter(nu.Fabric):
        pass

    bound = nu.context.FabricRef(Greeter).exists()
    launch = Launch(init=nu.Provide(Greeter, kwargs={}, body=nu.Noop()))
    tree = nu.mem.let(Local, Teleport(None, bound, W), w=launch)
    assert nu.run(tree, ctx)[0] is True
