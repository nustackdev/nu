"""Tests for nu_mem.JQueueRef — janus-backed queue ref."""

from __future__ import annotations

import asyncio
import threading

import pytest

from nu import Context, runtime
from nu.shapes import Shape
from nu_mem import JQueueRef, QueueClosed


class BufShape(Shape):
    queue = JQueueRef.slot(capacity=2, item_type=int)


class UnboundedBuf(Shape):
    queue = JQueueRef.slot(item_type=int)


@pytest.fixture
def ctx() -> tuple[Context, dict]:
    data: dict = {}
    return Context().bind(dict, data, BufShape), data


@pytest.fixture
def unbounded_ctx() -> Context:
    return Context().bind(dict, {}, UnboundedBuf)


def test_sync_round_trip(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    runtime.execute(BufShape.queue.put(1), c)
    runtime.execute(BufShape.queue.put(2), c)
    assert runtime.collect(BufShape.queue.qsize(), c) == [2]
    assert runtime.collect(BufShape.queue.get(), c) == [1]
    assert runtime.collect(BufShape.queue.get(), c) == [2]
    assert runtime.collect(BufShape.queue.qsize(), c) == [0]


async def test_async_round_trip(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    await runtime.aexecute(BufShape.queue.put(7), c)
    await runtime.aexecute(BufShape.queue.put(8), c)
    assert await runtime.acollect(BufShape.queue.get(), c) == [7]
    assert await runtime.acollect(BufShape.queue.get(), c) == [8]


def test_vivifies_in_backing_dict(ctx: tuple[Context, dict]) -> None:
    c, data = ctx
    assert "queue" not in data
    runtime.execute(BufShape.queue.put(1), c)
    assert "queue" in data
    assert type(data["queue"]).__name__ == "Queue"


def test_unbounded_default(unbounded_ctx: Context) -> None:
    for i in range(50):
        runtime.execute(UnboundedBuf.queue.put(i), unbounded_ctx)
    assert runtime.collect(UnboundedBuf.queue.qsize(), unbounded_ctx) == [50]


async def test_async_producer_thread_consumer_backpressure(
    ctx: tuple[Context, dict],
) -> None:
    """Capacity=2, 10 items: forces back-pressure across the bridge."""
    c, _ = ctx
    received: list[int] = []

    def consumer() -> None:
        while True:
            try:
                x = runtime.collect(BufShape.queue.get(), c)[0]
            except QueueClosed:
                break
            received.append(x)

    th = threading.Thread(target=consumer)
    th.start()

    for i in range(10):
        await runtime.aexecute(BufShape.queue.put(i), c)
    await runtime.aexecute(BufShape.queue.close(), c)

    await asyncio.get_running_loop().run_in_executor(None, th.join, 5.0)
    assert received == list(range(10))


def test_close_then_get_raises(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    runtime.execute(BufShape.queue.close(), c)
    with pytest.raises(QueueClosed):
        runtime.collect(BufShape.queue.get(), c)


def test_close_then_put_raises(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    runtime.execute(BufShape.queue.close(), c)
    with pytest.raises(QueueClosed):
        runtime.execute(BufShape.queue.put(1), c)


async def test_close_then_aget_raises(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    await runtime.aexecute(BufShape.queue.close(), c)
    with pytest.raises(QueueClosed):
        await runtime.acollect(BufShape.queue.get(), c)


def test_close_drains_pending_then_raises(ctx: tuple[Context, dict]) -> None:
    c, _ = ctx
    runtime.execute(BufShape.queue.put(7), c)
    runtime.execute(BufShape.queue.put(8), c)
    runtime.execute(BufShape.queue.close(), c)
    assert runtime.collect(BufShape.queue.get(), c) == [7]
    assert runtime.collect(BufShape.queue.get(), c) == [8]
    with pytest.raises(QueueClosed):
        runtime.collect(BufShape.queue.get(), c)
