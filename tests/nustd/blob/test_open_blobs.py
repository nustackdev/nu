"""Open blobs: put without a seal, append, seal, and reads that follow a blob as it grows.

The local backends hold open blobs; each runs here with small chunks and
batches, so a put or an append spans many commits. S3 holds none: it refuses
them, and reads its sealed blobs as before.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import multiprocessing
import os
import signal
import threading
import time

import pytest
from _support.blob_fixtures import leftovers
from _support.blob_workers import (
    LOCAL_KINDS,
    appender,
    follower,
    growing,
    make_small,
    stalled_writer,
)

from nustd.blob import (
    BlobIdle,
    BlobInfo,
    BlobNotFound,
    BlobSealed,
    BlobTooLarge,
    S3Backend,
)
from nustd.blob._base import new_id


DATA = bytes(range(256)) * 40  # 10240 bytes, past several chunks and batches


class BoomError(RuntimeError):
    pass


def failing(pieces=3, size=5000):
    for _ in range(pieces):
        yield b"y" * size
    raise BoomError("source died")


async def afailing(pieces=3, size=5000):
    for _ in range(pieces):
        yield b"y" * size
        await asyncio.sleep(0)
    raise BoomError("source died")


async def agen(*pieces):
    for piece in pieces:
        await asyncio.sleep(0)
        yield piece


@pytest.fixture(params=LOCAL_KINDS)
def local(request):
    return request.param


@pytest.fixture
def store(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    yield backend
    backend.close()


def later(delay, call, *args):
    """Run ``call`` in a thread after ``delay`` seconds; the thread, started."""

    def run():
        time.sleep(delay)
        call(*args)

    thread = threading.Thread(target=run)
    thread.start()
    return thread


# ---- the record --------------------------------------------------------------------------


def test_info_carries_sealed():
    info = BlobInfo(id=new_id(), size=3, sealed=False)
    assert info.to_dict()["sealed"] is False
    assert BlobInfo.from_dict(info.to_dict()) == info


def test_a_record_with_no_sealed_reads_as_sealed():
    assert BlobInfo.from_dict({"id": new_id(), "size": 1}).sealed is True


def test_supports_open(store):
    assert store.supports_open is True


# ---- put, append, seal -------------------------------------------------------------------


def test_plain_put_is_sealed(store):
    info = store.put(DATA)
    assert info.sealed
    assert store.info(info.id).sealed


def test_put_unsealed_then_append_then_seal(store):
    info = store.put(DATA[:3000], seal=False, mime="a/b", name="n")
    assert (info.size, info.sealed) == (3000, False)
    assert store.info(info.id) == info
    grown = store.append(info.id, DATA[3000:])
    assert (grown.size, grown.sealed) == (len(DATA), False)
    assert (grown.mime, grown.name, grown.created_at) == ("a/b", "n", info.created_at)
    sealed = store.seal(info.id)
    assert (sealed.size, sealed.sealed) == (len(DATA), True)
    assert store.info(info.id) == sealed
    assert store.read(info.id) == DATA
    assert leftovers(store) == []


def test_empty_open_blob(store):
    info = store.put(b"", seal=False)
    assert (info.size, info.sealed) == (0, False)
    assert store.exists(info.id)
    assert list(store.stream(info.id)) == []
    store.append(info.id, b"abc")
    assert store.seal(info.id).size == 3
    assert store.read(info.id) == b"abc"


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda data, tmp: data, id="bytes"),
        pytest.param(lambda data, tmp: memoryview(data), id="memoryview"),
        pytest.param(lambda data, tmp: io.BytesIO(data), id="file"),
        pytest.param(lambda data, tmp: [data[:7], data[7:]], id="iterable"),
        pytest.param(lambda data, tmp: (tmp / "p").write_bytes(data) and (tmp / "p"), id="path"),
    ],
)
def test_append_sources_across_chunk_edges(store, tmp_path, make_source):
    # Pieces of odd sizes: each append starts inside a short last chunk.
    bid = store.put(b"", seal=False).id
    expected = b""
    for index in range(8):
        piece = growing(index)
        store.append(bid, make_source(piece, tmp_path))
        expected += piece
        assert store.info(bid).size == len(expected)
        assert b"".join(store.stream(bid, step=777)) == expected
    store.seal(bid)
    assert store.read(bid) == expected
    assert store.read(bid, 1000, 5000) == expected[1000:5000]
    assert leftovers(store) == []


def test_seal_is_idempotent(store):
    bid = store.put(b"x", seal=False).id
    first = store.seal(bid)
    assert store.seal(bid) == first
    plain = store.put(b"y")
    assert store.seal(plain.id) == plain


def test_append_to_a_sealed_blob_raises(store):
    bid = store.put(b"x").id
    with pytest.raises(BlobSealed):
        store.append(bid, b"more")
    with pytest.raises(BlobSealed):
        store.append(bid, iter([b"more"]))
    assert store.read(bid) == b"x"


def test_append_and_seal_of_a_missing_blob_raise(store):
    with pytest.raises(BlobNotFound):
        store.append(new_id(), b"x")
    with pytest.raises(BlobNotFound):
        store.seal(new_id())


@pytest.mark.parametrize("call", ["append", "seal"])
def test_bad_id_refused(store, call):
    with pytest.raises(ValueError, match="32 lowercase hex"):
        getattr(store, call)("nope", *([b"x"] if call == "append" else []))


def test_append_refuses_a_str(store):
    bid = store.put(b"", seal=False).id
    with pytest.raises(TypeError):
        store.append(bid, "text")


@pytest.mark.parametrize("seal", [True, False], ids=["sealed", "open"])
def test_failed_put_leaves_nothing(store, seal):
    bid = new_id()
    with pytest.raises(BoomError):
        store.put(failing(), blob_id=bid, seal=seal)
    assert not store.exists(bid)
    with pytest.raises(BlobNotFound):
        store.info(bid)
    assert leftovers(store) == []
    assert store.put(b"again", blob_id=bid).id == bid


def test_failed_append_keeps_what_it_committed(store):
    bid = store.put(b"head", seal=False).id
    with pytest.raises(BoomError):
        store.append(bid, failing())
    info = store.info(bid)
    assert not info.sealed
    assert 4 < info.size < 4 + 15000  # some batches landed, never the bytes in hand
    assert store.read(bid, 0, info.size) == (b"head" + b"y" * 15000)[: info.size]
    assert leftovers(store) == []
    store.append(bid, b"tail")
    store.seal(bid)
    assert store.read(bid) == (b"head" + b"y" * 15000)[: info.size] + b"tail"


def test_too_large_append_keeps_the_blob_open(store, monkeypatch):
    bid = store.put(b"x" * 100, seal=False).id
    monkeypatch.setattr(store, "max_size", 150, raising=False)
    with pytest.raises(BlobTooLarge):
        store.append(bid, b"y" * 100)
    assert store.info(bid).size == 100
    assert not store.info(bid).sealed


async def test_async_put_append_seal(store):
    info = await store.aput(agen(DATA[:5000], DATA[5000:6000]), seal=False)
    assert (info.size, info.sealed) == (6000, False)
    await store.aappend(info.id, agen(DATA[6000:9000]))
    await store.aappend(info.id, DATA[9000:])
    sealed = await store.aseal(info.id)
    assert sealed.sealed
    assert await store.aread(info.id) == DATA
    assert await store.aseal(info.id) == sealed


async def test_async_failed_append_keeps_what_it_committed(store):
    bid = (await store.aput(b"", seal=False)).id
    with pytest.raises(BoomError):
        await store.aappend(bid, afailing())
    info = await store.ainfo(bid)
    assert not info.sealed
    assert await store.aread(bid, 0, info.size) == b"y" * info.size
    assert leftovers(store) == []
    await store.aseal(bid)
    with pytest.raises(BlobSealed):
        await store.aappend(bid, b"x")


async def test_async_failed_put_leaves_nothing(store):
    bid = new_id()
    with pytest.raises(BoomError):
        await store.aput(afailing(), blob_id=bid, seal=False)
    assert not await store.aexists(bid)
    assert leftovers(store) == []


# ---- one writer at a time ----------------------------------------------------------------


def test_concurrent_appends_take_turns(store):
    # Each append spans many batches; turns mean neither splits the other.
    bid = store.put(b"", seal=False).id
    pieces = {name: [name.encode() * 1000] * 20 for name in ("a", "b")}
    threads = [
        threading.Thread(target=store.append, args=(bid, iter(pieces[name]))) for name in pieces
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    data = store.read(bid, 0, 40_000)
    assert sorted((data[:20_000], data[20_000:])) == [b"a" * 20_000, b"b" * 20_000]
    assert leftovers(store) == []


def test_seal_waits_for_the_append_in_flight(store):
    bid = store.put(b"", seal=False).id
    started, go = threading.Event(), threading.Event()

    def slow():
        yield b"z" * 6000  # past one batch: the append holds the blob
        started.set()
        go.wait(10)
        yield b"z" * 6000

    writer = threading.Thread(target=store.append, args=(bid, slow()))
    writer.start()
    try:
        assert started.wait(10)
        sealing = later(0, store.seal, bid)
        time.sleep(0.3)
        assert not store.info(bid).sealed  # the seal waits its turn
        go.set()
        writer.join(10)
        sealing.join(10)
        info = store.info(bid)
        assert (info.size, info.sealed) == (12_000, True)
    finally:
        go.set()
        writer.join(10)


# ---- reading an open blob ----------------------------------------------------------------


def test_plain_stream_of_an_open_blob_reads_what_is_there(store):
    bid = store.put(DATA[:5000], seal=False).id
    assert b"".join(store.stream(bid, step=1000)) == DATA[:5000]
    assert store.read(bid, 1000, 3000) == DATA[1000:3000]


def test_follow_reads_until_sealed(store):
    bid = store.put(DATA[:1000], seal=False).id

    def write():
        for offset in range(1000, len(DATA), 1500):
            time.sleep(0.02)
            store.append(bid, DATA[offset : offset + 1500])
        store.seal(bid)

    writer = later(0, write)
    try:
        assert b"".join(store.stream(bid, step=700, follow=True)) == DATA
    finally:
        writer.join(10)


def test_follow_from_an_offset_and_to_an_end_past_the_size(store):
    bid = store.put(DATA[:1000], seal=False).id
    writer = later(0.1, store.append, bid, DATA[1000:6000])
    try:
        # Waits for the bytes up to 4000, then ends: no seal needed.
        assert b"".join(store.stream(bid, 500, 4000, follow=True)) == DATA[500:4000]
    finally:
        writer.join(10)
    assert not store.info(bid).sealed


def test_follow_of_a_sealed_blob_is_a_plain_read(store):
    bid = store.put(DATA).id
    assert b"".join(store.stream(bid, 100, follow=True, idle=0)) == DATA[100:]


def test_follow_raises_idle_without_growth(store):
    bid = store.put(b"abc", seal=False).id
    pieces = store.stream(bid, follow=True, idle=0.2)
    assert next(pieces) == b"abc"
    began = time.monotonic()
    with pytest.raises(BlobIdle):
        next(pieces)
    assert 0.15 < time.monotonic() - began < 2


def test_idle_counts_from_the_last_growth(store):
    bid = store.put(b"", seal=False).id

    def write():
        for _ in range(5):
            time.sleep(0.1)
            store.append(bid, b"x")
        store.seal(bid)

    writer = later(0, write)
    try:
        assert b"".join(store.stream(bid, follow=True, idle=0.4)) == b"x" * 5
    finally:
        writer.join(10)


def test_negative_idle_is_refused(store):
    with pytest.raises(ValueError, match="idle"):
        store.stream(new_id(), follow=True, idle=-1)


def test_delete_mid_follow_raises(store):
    bid = store.put(b"abc", seal=False).id
    pieces = store.stream(bid, follow=True)
    assert next(pieces) == b"abc"
    deleting = later(0.1, store.delete, bid)
    try:
        with pytest.raises(BlobNotFound):
            next(pieces)
    finally:
        deleting.join(10)


def test_follower_of_a_failed_put_gets_not_found(store):
    bid = new_id()
    landed, go = threading.Event(), threading.Event()

    def dying():
        yield b"y" * 9000  # two batches land
        landed.set()
        go.wait(10)
        raise BoomError("source died")

    def put():
        with pytest.raises(BoomError):
            store.put(dying(), blob_id=bid)

    writer = threading.Thread(target=put)
    writer.start()
    try:
        assert landed.wait(10)
        pieces = store.stream(bid, follow=True)
        assert len(next(pieces)) > 0
        go.set()
        with pytest.raises(BlobNotFound):
            for _ in pieces:
                pass
    finally:
        go.set()
        writer.join(10)


def test_read_of_an_open_blob_waits_for_the_seal(store):
    bid = store.put(b"abc", seal=False).id

    def finish():
        store.append(bid, b"def")
        store.seal(bid)

    writer = later(0.2, finish)
    try:
        assert store.read(bid) == b"abcdef"
        assert store.read(bid, 1, 2) == b"b"  # within the size: no wait
    finally:
        writer.join(10)


def test_read_of_a_range_past_the_size_waits_for_it(store):
    bid = store.put(b"abc", seal=False).id
    writer = later(0.1, store.append, bid, b"defgh")
    try:
        assert store.read(bid, 2, 6) == b"cdef"
    finally:
        writer.join(10)


async def test_astream_follows_until_sealed(store):
    bid = (await store.aput(b"ab", seal=False)).id

    async def write():
        for piece in (b"cd", b"ef"):
            await asyncio.sleep(0.05)
            await store.aappend(bid, piece)
        await store.aseal(bid)

    task = asyncio.create_task(write())
    got = b"".join([piece async for piece in store.astream(bid, follow=True)])
    await task
    assert got == b"abcdef"


async def test_aread_of_an_open_blob_waits_on_the_loop(store):
    bid = (await store.aput(b"ab", seal=False)).id

    async def finish():
        await asyncio.sleep(0.1)
        await store.aappend(bid, b"cd")
        await store.aseal(bid)

    task = asyncio.create_task(finish())
    assert await store.aread(bid) == b"abcd"
    await task


async def test_cancelled_follow_stops_at_once(store):
    bid = (await store.aput(b"ab", seal=False)).id

    async def drain():
        return [piece async for piece in store.astream(bid, follow=True)]

    task = asyncio.create_task(drain())
    await asyncio.sleep(0.3)
    began = time.monotonic()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert time.monotonic() - began < 0.2


async def test_astream_idle(store):
    bid = (await store.aput(b"ab", seal=False)).id
    with pytest.raises(BlobIdle):
        async for _ in store.astream(bid, follow=True, idle=0.1):
            pass


async def test_cancelled_aappend_waiting_for_its_turn_holds_nothing(store):
    bid = (await store.aput(b"", seal=False)).id
    started, go = threading.Event(), threading.Event()

    def slow():
        yield b"z" * 6000
        started.set()
        go.wait(10)

    writer = threading.Thread(target=store.append, args=(bid, slow()))
    writer.start()
    try:
        await asyncio.to_thread(started.wait, 10)
        waiting = asyncio.create_task(store.aappend(bid, b"late"))
        await asyncio.sleep(0.2)
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
    finally:
        go.set()
        await asyncio.to_thread(writer.join, 10)
    await store.aappend(bid, b"next")  # nothing was left holding the blob
    assert (await store.aread(bid, 6000, 6004)) == b"next"


# ---- across processes --------------------------------------------------------------------


@pytest.mark.timeout(120)
def test_follower_in_another_process(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    bid = backend.put(b"start", seal=False).id
    ctx = multiprocessing.get_context("spawn")
    ready, out = ctx.Queue(), ctx.Queue()
    child = ctx.Process(target=follower, args=(local, str(store_path), bid, ready, out))
    child.start()
    try:
        assert ready.get(timeout=60) == "ready"
        expected = b"start"
        for index in range(30):
            backend.append(bid, growing(index))
            expected += growing(index)
            time.sleep(0.01)
        backend.seal(bid)
        assert out.get(timeout=60) == ("ok", hashlib.sha256(expected).hexdigest(), len(expected))
    finally:
        child.join(timeout=30)
        backend.close()
    assert child.exitcode == 0


@pytest.mark.timeout(120)
def test_writer_in_another_process(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    bid = backend.put(b"", seal=False).id
    ctx = multiprocessing.get_context("spawn")
    out = ctx.Queue()
    child = ctx.Process(target=appender, args=(local, str(store_path), bid, 30, out))
    child.start()
    try:
        data = b"".join(backend.stream(bid, step=1000, follow=True, idle=30))
        expected = b"".join(growing(index) for index in range(30))
        assert data == expected
        assert out.get(timeout=60) == len(expected)
    finally:
        child.join(timeout=30)
        backend.close()
    assert child.exitcode == 0


def _kill_stalled(local, store_path, bid, mode):
    ctx = multiprocessing.get_context("spawn")
    ready, go = ctx.Queue(), ctx.Queue()
    child = ctx.Process(target=stalled_writer, args=(local, str(store_path), bid, mode, ready, go))
    child.start()
    try:
        assert ready.get(timeout=60) == "stalled"
        return child
    except BaseException:
        child.kill()
        child.join(timeout=30)
        raise


@pytest.mark.timeout(120)
def test_killed_put_reads_as_missing_at_once(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    bid = new_id()
    try:
        child = _kill_stalled(local, store_path, bid, "put")
        try:
            info = backend.info(bid)
            assert (info.size > 0, info.sealed) == (True, False)  # readable mid-put
            pieces = backend.stream(bid, follow=True, idle=30)
            assert next(pieces)
            os.kill(child.pid, signal.SIGKILL)
        finally:
            child.join(timeout=30)
        with pytest.raises(BlobNotFound):
            for _ in pieces:
                pass
        assert not backend.exists(bid)
        with pytest.raises(BlobNotFound):
            backend.seal(bid)
        with pytest.raises(BlobNotFound):
            backend.append(bid, b"x")
    finally:
        backend.close()


@pytest.mark.timeout(120)
def test_killed_append_leaves_the_blob_open_with_its_commits(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    try:
        bid = backend.put(b"head", seal=False).id
        child = _kill_stalled(local, store_path, bid, "append")
        try:
            committed = backend.info(bid).size
            assert committed > 4
            os.kill(child.pid, signal.SIGKILL)
        finally:
            child.join(timeout=30)
        backend.append(bid, b"tail")  # the dead writer's hold is gone
        info = backend.seal(bid)
        assert info.size == committed + 4
        assert backend.read(bid) == (b"head" + b"x" * 20_000)[:committed] + b"tail"
    finally:
        backend.close()


# ---- s3 holds no open blobs --------------------------------------------------------------


@pytest.fixture
def s3(moto_s3):
    backend = S3Backend("nu-blob-test", prefix="open/")
    backend.open()
    yield backend
    backend.close()


def no_requests(backend, monkeypatch):
    sent = []
    for name in ("put_object", "create_multipart_upload", "head_object", "get_object"):
        real = getattr(backend._client, name)
        monkeypatch.setattr(
            backend._client,
            name,
            lambda *a, _real=real, _n=name, **k: sent.append(_n) or _real(*a, **k),
        )
    return sent


def test_s3_does_not_support_open(s3):
    assert s3.supports_open is False


def test_s3_refuses_an_unsealed_put_before_any_request(s3, monkeypatch):
    sent = no_requests(s3, monkeypatch)
    with pytest.raises(NotImplementedError, match="no open blobs"):
        s3.put(b"x", seal=False)
    with pytest.raises(NotImplementedError, match="no open blobs"):
        s3.put(iter([b"x"]), seal=False)
    assert sent == []


async def test_s3_refuses_an_unsealed_aput(s3):
    with pytest.raises(NotImplementedError, match="no open blobs"):
        await s3.aput(agen(b"x"), seal=False)
    with pytest.raises(NotImplementedError, match="no open blobs"):
        await s3.aput(b"x", seal=False)


async def test_s3_refuses_append(s3):
    bid = s3.put(b"x").id
    with pytest.raises(NotImplementedError, match="no open blobs"):
        s3.append(bid, b"y")
    with pytest.raises(NotImplementedError, match="no open blobs"):
        await s3.aappend(bid, b"y")
    with pytest.raises(NotImplementedError, match="no open blobs"):
        await s3.aappend(bid, agen(b"y"))
    assert s3.read(bid) == b"x"


async def test_s3_blobs_are_sealed_and_seal_is_a_no_op(s3):
    info = s3.put(DATA)
    assert info.sealed
    assert s3.info(info.id).sealed
    assert s3.seal(info.id) == s3.info(info.id)
    assert (await s3.aseal(info.id)).sealed
    with pytest.raises(BlobNotFound):
        s3.seal(new_id())


async def test_s3_follow_is_a_plain_read(s3):
    bid = s3.put(DATA).id
    assert b"".join(s3.stream(bid, 10, follow=True, idle=0)) == DATA[10:]
    assert b"".join([p async for p in s3.astream(bid, follow=True, idle=0)]) == DATA
    assert s3.read(bid) == DATA
