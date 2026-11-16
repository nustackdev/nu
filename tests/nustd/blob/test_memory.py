"""A put from a stream never holds the whole value in memory, per backend."""

from __future__ import annotations

import multiprocessing
import sys
import time
import tracemalloc
from pathlib import Path

import pytest
from _support.blob_workers import LOCAL_KINDS, putter


@pytest.fixture(params=LOCAL_KINDS)
def kind(request):
    # Local backends only: moto keeps every byte it is sent in this process
    # (and joins the parts whole on complete), so tracemalloc over it would
    # measure moto. The s3 backend's memory is measured in test_s3.py, over
    # a client whose sends go nowhere.
    return request.param


SIZE = 64 << 20
STEP = 1 << 20


def pieces():
    for index in range(SIZE // STEP):
        yield bytes([index % 256]) * STEP


async def apieces():
    for piece in pieces():
        yield piece


def check_content(backend, blob_id):
    assert backend.info(blob_id).size == SIZE
    for index in (0, 17, SIZE // STEP - 1):
        assert backend.read(blob_id, index * STEP, index * STEP + 3) == bytes([index % 256]) * 3


def test_iterable_put_peak_is_flat(backend):
    tracemalloc.start()
    try:
        info = backend.put(pieces())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 8 * STEP, f"peak {peak} for a {SIZE} byte put"
    check_content(backend, info.id)


async def test_async_iterable_put_peak_is_flat(backend):
    tracemalloc.start()
    try:
        info = await backend.aput(apieces())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 8 * STEP, f"peak {peak} for a {SIZE} byte put"
    check_content(backend, info.id)


def test_stream_read_peak_is_flat(backend):
    info = backend.put(pieces())
    tracemalloc.start()
    try:
        total = sum(len(piece) for piece in backend.stream(info.id))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert total == SIZE
    assert peak < 8 * STEP


def rss_anon_kib(pid):
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("RssAnon:"):
            return int(line.split()[1])
    raise AssertionError("no RssAnon")


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads /proc")
def test_process_memory_stays_flat(kind, store_path):
    # tracemalloc sees Python allocations only; this watches the whole
    # process from outside, C heap included (LMDB's dirty pages live there).
    ctx = multiprocessing.get_context("spawn")
    ready, go = ctx.Queue(), ctx.Queue()
    child = ctx.Process(target=putter, args=(kind, str(store_path), SIZE, ready, go))
    child.start()
    try:
        assert ready.get(timeout=60) == "ready"
        base = rss_anon_kib(child.pid)
        go.put("put")
        peak = base
        while ready.empty():
            peak = max(peak, rss_anon_kib(child.pid))
            time.sleep(0.001)
        assert ready.get() == SIZE
        go.put("done")
    finally:
        child.join(timeout=30)
    grown = (peak - base) * 1024
    assert grown < SIZE // 4, f"anon memory grew {grown} bytes for a {SIZE} byte put"
