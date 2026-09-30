"""``nustd.mp.MpWorker`` over a real child process: what crosses the pipe.

Everything the parent and the worker exchange goes through ``nu.lang.wire``,
so a tree over a class no module can name, one defined inside the test, runs
in the child all the same. Real processes, no mocks.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nustd.mp import MpWorker, Teleport


pytestmark = pytest.mark.slow


def _on_a_worker(body: nu.Nu) -> nu.Nu:
    return nu.Provide(MpWorker, {"name": "nu-test-mp-wire"}, Teleport(body))


def test_a_tree_over_a_local_shape_runs_on_the_worker() -> None:
    class Tally(nu.Shape):
        n = nu.mem.IntRef.slot()

    body = nu.mem.Frame(Tally, nu.Add(Tally.n, 1), n=41)
    assert nu.run(_on_a_worker(body))[0] == 42


async def test_a_let_runs_on_the_worker() -> None:
    body = nu.mem.let(41, lambda n: nu.Add(n, 1))
    assert (await nu.arun(_on_a_worker(body)))[0] == 42


def test_an_init_holding_a_local_class_reaches_the_worker() -> None:
    class Greeter:
        def hello(self) -> str:
            return "hi"

    init = nu.Provide(Greeter, {}, nu.Noop())
    worker = MpWorker(init=init, name="nu-test-mp-init")
    worker.setup(nu.Context())
    try:
        bound = nu.context.FabricRef(Greeter).exists()
        assert asyncio.run(worker.aexecute(bound)) is True
    finally:
        worker.cleanup()
