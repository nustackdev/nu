"""The reason ``nustd.valkey`` exists: kv change notifications across processes.

A private Valkey server, two ``mp_pool`` workers, each holding its own
``sqlite_navigator_redis`` stack on the same SQLite file and pointed at the
server by ``url_for(data_dir)``. A write in worker A has to wake a resident
reaction in worker B.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path

import pytest
from _support.valkey_shapes import B_BODY, B_INIT, READ_LAST, READ_WAKES, a_burst, a_set

import nu
import nustd
from nustd.mp_pool import PoolRef, WorkerPool
from nustd.valkey import ValkeyServer, socket_path_for, url_for


pytestmark = pytest.mark.slow

POOL = PoolRef()


def _await_true(fn, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def data_dir():
    d = tempfile.mkdtemp(prefix="nu-vk-test-")
    try:
        yield d
    finally:
        sock = Path(socket_path_for(d))
        if sock.exists():
            sock.unlink()
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def ctx(data_dir):
    srv = ValkeyServer(data_dir=data_dir)
    srv.setup(None)
    pool = WorkerPool(name="nu-test-vk")
    pool.setup(None)
    try:
        yield nu.Context().bind(ValkeyServer, srv).bind(WorkerPool, pool)
    finally:
        pool.cleanup()
        srv.cleanup()


def test_a_write_in_one_worker_wakes_a_reaction_in_another(ctx, data_dir):
    # Built from the dir alone, as a worker or a caller outside the tree would.
    stack = nustd.kv.sqlite_navigator_redis(
        str(Path(data_dir, "kv.sqlite")),
        redis_url=url_for(data_dir),
    )
    # The worker ids are the runs' values, carried to the next run as literals.
    a = nu.Literal(nu.run(POOL.launch(stack), ctx)[0])
    b = nu.Literal(nu.run(POOL.launch(stack), ctx)[0])
    nu.run(POOL.teleport(B_INIT, b) >> POOL.dispatch(B_BODY, b), ctx)

    def read(term):
        return nu.run(POOL.teleport(term, b), ctx)[0]

    # B's subscription registers with the server asynchronously after the
    # dispatch is acked, so keep writing until the first wake lands.
    def wrote_and_woke():
        nu.run(POOL.teleport(a_set(42), a), ctx)
        return read(READ_WAKES) >= 1

    assert _await_true(wrote_and_woke), "B never woke on A's write"
    assert _await_true(lambda: read(READ_LAST) == 42)

    wakes = read(READ_WAKES)
    nu.run(POOL.teleport(a_burst(1000, 100), a), ctx)
    # Wakes coalesce under a burst; what must hold is that B catches up to the
    # last value written and woke at least once more.
    assert _await_true(lambda: read(READ_LAST) == 1099), read(READ_LAST)
    assert read(READ_WAKES) > wakes
