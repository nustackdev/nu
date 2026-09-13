"""``served_observer`` / ``proxy_observer``: a change feed across a socket.

A proxy carries calls, not notifications, so a process holding nothing but a
proxied Navigator hears none of the writes it did not make. These two presets
are the ears. What is checked here is the whole round trip over a real process
boundary, plus the one hazard the hosted layer exists for: a subscriber that
dies must not leave a receiver behind to fail on every write after.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import signal
import socket
import time

import pytest
from _support.observer_workers import child_main

from nu.context.fabric import With
from nu.core.reactive import ObserverProtocol
from nu.kv import proxy_observer, served_observer
from nu.kv.fabrics import (
    Codec,
    HostedObserver,
    InMemoryObserver,
    InMemoryPublisher,
    InMemoryStorage,
    InMemoryTransport,
    Navigator,
    noop_kwargs,
)
from nu.lang import Context
from nu.proxy import InvisiblesProxy, InvisiblesServer
from virtuals.tkv.filter import PrefixFilter
from virtuals.tkv.observer import SubscriptionOptions


PREFIX = ("demo",)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _options() -> SubscriptionOptions:
    return SubscriptionOptions(filter=PrefixFilter(prefix=PREFIX))


class _Head:
    """A store, its observer, and that observer on a socket. The parent's side."""

    def __init__(self, address: str) -> None:
        ctx = Context().bind(Codec, Codec(**noop_kwargs()))
        self._parts = []
        for part, binding in (
            (InMemoryTransport(), InMemoryTransport),
            (InMemoryPublisher(), InMemoryPublisher),
            (InMemoryObserver(), ObserverProtocol),
            (InMemoryStorage(), InMemoryStorage),
            (Navigator(storage_type=InMemoryStorage), Navigator),
        ):
            part.setup(ctx)
            ctx = ctx.bind(binding, part)
            self._parts.append(part)
        self.storage = self._parts[3]
        self.hosted = HostedObserver()
        self.hosted.setup(ctx)
        ctx = ctx.bind(HostedObserver, self.hosted)
        self.server = InvisiblesServer(target=HostedObserver, address=address)
        self.server.setup(ctx)
        self.ctx = ctx

    def write(self, value: int) -> None:
        with self.storage.transaction() as txn:
            txn.put((*PREFIX, "counter"), value)

    def close(self) -> None:
        self.server.cleanup()
        self.hosted.cleanup()
        for part in reversed(self._parts):
            part.cleanup()


@pytest.fixture
def head():
    address = f"127.0.0.1:{_free_port()}"
    head = _Head(address)
    head.address = address
    try:
        yield head
    finally:
        head.close()


def _drain(out, kind: str, timeout: float = 20.0):
    """Next message of ``kind`` off the child's queue, or fail."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        got = out.get(timeout=timeout)
        if got[0] == kind:
            return got[1]
    pytest.fail(f"child never reported {kind}")
    return None


# --- shape ------------------------------------------------------------------


def test_served_observer_provides_the_hosted_observer_and_a_server():
    bracket = served_observer("127.0.0.1:19000")
    assert isinstance(bracket, With)
    brackets = bracket._payload["brackets"]
    assert [b._payload["cls"] for b in brackets] == [HostedObserver, InvisiblesServer]
    assert brackets[1]._payload["kwargs"]["target"] is HostedObserver


def test_proxy_observer_is_a_proxy_bound_under_the_protocol():
    bracket = proxy_observer("127.0.0.1:19000")
    assert isinstance(bracket, InvisiblesProxy)
    assert bracket._payload["target"] is ObserverProtocol
    # The far side calls back into this process, so it has to be serving.
    assert bracket._payload["client_kwargs"]["bg_serve"] is True


# --- the feature ------------------------------------------------------------


def test_child_hears_a_write_the_parent_made(head):
    mpctx = mp.get_context("spawn")
    out = mpctx.Queue()
    child = mpctx.Process(target=child_main, args=(head.address, out, PREFIX))
    child.start()
    try:
        _drain(out, "ready")
        head.write(1)
        assert _drain(out, "key") == (*PREFIX, "counter")
    finally:
        child.kill()
        child.join(timeout=10)


def test_a_dead_child_leaves_no_receiver_behind(head):
    mpctx = mp.get_context("spawn")
    out = mpctx.Queue()
    child = mpctx.Process(target=child_main, args=(head.address, out, PREFIX))
    child.start()
    try:
        _drain(out, "ready")
        head.write(1)
        _drain(out, "key")
        sub = head.hosted._open[0]
        assert len(sub.receivers) == 1

        os.kill(child.pid, signal.SIGKILL)
        child.join(timeout=10)

        # One failed round trip, then the corpse is gone and stays gone.
        head.write(2)
        deadline = time.monotonic() + 10.0
        while sub.receivers and time.monotonic() < deadline:
            time.sleep(0.05)
        assert sub.receivers == ()
        head.write(3)
        head.write(4)
        assert sub.receivers == ()
        # Nobody left to serve, so the subscription closed itself.
        assert head.hosted._open == []
    finally:
        child.kill()
        child.join(timeout=10)


def test_local_subscribers_still_hear_everything(head):
    """Serving the observer does not take the process's own feed away."""
    heard = []
    sub = head.ctx.get(ObserverProtocol).subscribe(_options())
    sub.bind(lambda key: heard.append(tuple(key)))
    try:
        head.write(1)
        head.write(2)
        deadline = time.monotonic() + 5.0
        while len(heard) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert heard == [(*PREFIX, "counter"), (*PREFIX, "counter")]
    finally:
        sub.close()
