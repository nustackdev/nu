"""What only the LMDB backend promises: its chunks, its claims, its env, its map."""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import os
import signal
import sys
import threading

import pytest
from _support.blob_fixtures import leftovers
from _support.blob_workers import CONTESTED, race_content, racer, stalled_putter

from nustd.blob import BlobExists, BlobNotFound, BlobTooLarge, LMDBBackend
from nustd.blob._base import new_id
from nustd.blob.backends.lmdb import DEFAULT_MAP_SIZE, DEFAULT_WRITEMAP, MAX_CHUNK


@pytest.fixture
def env(tmp_path):
    backend = LMDBBackend(tmp_path / "env")
    backend.open()
    yield backend
    backend.close()


def test_max_size_set_by_hand_is_refused(env, monkeypatch):
    monkeypatch.setattr(env, "max_size", 10)
    with pytest.raises(BlobTooLarge):
        env.put(b"x" * 11)


@pytest.mark.parametrize("size", [0, MAX_CHUNK + 1])
def test_chunk_size_bounds(size):
    with pytest.raises(ValueError, match="chunk_size"):
        LMDBBackend("unused", chunk_size=size)


def test_batch_size_bounds():
    with pytest.raises(ValueError, match="batch_size"):
        LMDBBackend("unused", batch_size=0)


def test_default_map_is_sparse(env):
    data = env.path / "data.mdb"
    env.put(b"x" * 100_000)
    assert env.map_size == DEFAULT_MAP_SIZE == 1 << 40
    assert data.stat().st_blocks * 512 < 64 << 20


def test_writemap_default_follows_the_platform():
    # macOS pays per GiB of map on every writemap commit: 14 s a put at 1 TiB.
    assert DEFAULT_WRITEMAP is (sys.platform != "darwin")
    assert LMDBBackend("unused").writemap is DEFAULT_WRITEMAP


@pytest.mark.parametrize("writemap", [False, True])
def test_either_writemap_puts_and_reads(tmp_path, writemap):
    # A small map keeps the writemap run fast on macOS too.
    backend = LMDBBackend(tmp_path / "env", map_size=1 << 30, writemap=writemap)
    backend.open()
    info = backend.put(iter([b"a", b"b"]))
    assert backend.read(info.id) == b"ab"
    backend.close()


def test_chunks_and_meta_in_one_txn(env):
    info = env.put(b"abc", mime="m")
    raw = bytes.fromhex(info.id)
    with env._env.begin() as txn:
        assert txn.get(raw + (0).to_bytes(8, "big"), db=env._data) == b"abc"
        assert txn.get(info.id.encode(), db=env._meta) is not None
    env.delete(info.id)
    with env._env.begin() as txn:
        assert txn.get(raw + (0).to_bytes(8, "big"), db=env._data) is None
        assert txn.get(info.id.encode(), db=env._meta) is None


def active_readers(backend):
    rows = backend._env.readers().splitlines()[1:]
    return [row for row in rows if row.split()[-1] != "-"]


def test_stream_holds_no_reader_between_pulls(env):
    info = env.put(b"x" * 1000)
    pieces = env.stream(info.id, step=100)
    assert next(pieces) == b"x" * 100
    assert active_readers(env) == []
    assert b"".join(pieces) == b"x" * 900


def test_closed_env_refuses(tmp_path):
    backend = LMDBBackend(tmp_path / "env")
    with pytest.raises(RuntimeError, match="not open"):
        backend.read(new_id())
    backend.open()
    backend.close()
    with pytest.raises(RuntimeError, match="not open"):
        backend.put(b"x")


def test_reopen_sees_blobs(tmp_path):
    first = LMDBBackend(tmp_path / "env")
    first.open()
    info = first.put(b"kept", name="k")
    first.close()
    second = LMDBBackend(tmp_path / "env")
    second.open()
    assert second.info(info.id) == info
    second.close()


@pytest.mark.parametrize("size", [300, 1000, 5000], ids=["shorter", "same", "longer"])
def test_stream_refuses_a_blob_replaced_mid_stream(env, size):
    bid = new_id()
    env.put(b"a" * 1000, blob_id=bid)
    pieces = env.stream(bid, step=100)
    assert next(pieces) == b"a" * 100
    env.delete(bid)
    env.put(b"b" * size, blob_id=bid)
    with pytest.raises(BlobNotFound):
        next(pieces)


def test_stream_raises_on_a_blob_deleted_mid_stream(env):
    info = env.put(b"a" * 1000)
    pieces = env.stream(info.id, step=100)
    next(pieces)
    env.delete(info.id)
    with pytest.raises(BlobNotFound):
        next(pieces)


# ---- chunks --------------------------------------------------------------------------------


def pattern(size):
    return bytes(range(251)) * (size // 251) + bytes(range(size % 251))


def chunked(tmp_path, chunk, batch):
    backend = LMDBBackend(tmp_path / "env", chunk_size=chunk, batch_size=batch)
    backend.open()
    return backend


def chunk_count(backend, blob_id):
    raw = bytes.fromhex(blob_id)
    with backend._env.begin() as txn:
        return sum(1 for key, _ in txn.cursor(db=backend._data) if key[:16] == raw)


def sources(data, tmp_path):
    path = tmp_path / "src.bin"
    path.write_bytes(data)
    return {
        "bytes": lambda: data,
        "path": lambda: path,
        "iterable": lambda: (data[i : i + 333] for i in range(0, len(data), 333)),
        "big-pieces": lambda: (data[i : i + 5000] for i in range(0, len(data), 5000)),
        "file": lambda: path.open("rb"),
    }


SOURCES = ["bytes", "path", "iterable", "big-pieces", "file"]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize(
    ("chunk", "batch", "size"),
    [
        (1000, 3000, 10_000),  # on a chunk edge, past several batches
        (1000, 3000, 9_999),  # one short of an edge
        (1000, 3000, 10_001),  # one past an edge
        (1000, 3000, 3_000),  # exactly one batch
        (1000, 1, 2_500),  # a batch smaller than a chunk: one chunk per txn
        (4096, 1 << 20, 50_000),  # one batch, many chunks
        (7, 21, 1_000),  # tiny chunks
        (1 << 20, 1 << 20, 1_000),  # one short chunk
    ],
)
def test_multi_chunk_round_trip(tmp_path, source, chunk, batch, size):
    data = pattern(size)
    backend = chunked(tmp_path, chunk, batch)
    try:
        info = backend.put(sources(data, tmp_path)[source](), mime="x/y")
        assert info.size == size
        assert chunk_count(backend, info.id) == -(-size // chunk)
        assert backend.read(info.id) == data
        assert backend.info(info.id) == info
        assert leftovers(backend) == []
    finally:
        backend.close()


@pytest.mark.parametrize("step", [1, 999, 1000, 1001, 2500, 1 << 20])
def test_ranges_across_chunk_edges(tmp_path, step):
    data = pattern(10_001)
    backend = chunked(tmp_path, 1000, 3000)
    try:
        bid = backend.put(data).id
        for start, end in [(0, None), (999, 1001), (1000, 2000), (1500, 7321), (9999, None)]:
            expected = data[start:end]
            assert backend.read(bid, start, end) == expected
            pieces = list(backend.stream(bid, start, end, step=step))
            assert b"".join(pieces) == expected
            assert all(len(piece) == step for piece in pieces[:-1])
    finally:
        backend.close()


async def test_async_multi_batch_put(tmp_path):
    data = pattern(10_001)

    async def pieces():
        for offset in range(0, len(data), 777):
            await asyncio.sleep(0)
            yield data[offset : offset + 777]

    backend = chunked(tmp_path, 1000, 3000)
    try:
        info = await backend.aput(pieces())
        assert await backend.aread(info.id) == data
        assert b"".join([piece async for piece in backend.astream(info.id, step=1234)]) == data
        assert leftovers(backend) == []
    finally:
        backend.close()


def test_store_mixes_chunk_sizes(tmp_path):
    small = LMDBBackend(tmp_path / "env", chunk_size=100)
    big = LMDBBackend(tmp_path / "env", chunk_size=4096)
    small.open()
    big.open()
    try:
        data = pattern(5000)
        a, b = small.put(data).id, big.put(data).id
        assert chunk_count(small, a) == 50
        assert chunk_count(small, b) == 2
        # Each blob reads by the chunk size it was put with, whoever reads it.
        assert big.read(a, 950, 1050) == small.read(b, 950, 1050) == data[950:1050]
    finally:
        small.close()
        big.close()


def test_delete_clears_every_chunk(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    try:
        neighbour = backend.put(pattern(1000)).id
        bid = backend.put(pattern(1000)).id
        assert backend.delete(bid)
        assert chunk_count(backend, bid) == 0
        assert backend.read(neighbour) == pattern(1000)
        assert not backend.delete(bid)
    finally:
        backend.close()


# ---- puts that fail, claims, the sweep -----------------------------------------------------


class BoomError(RuntimeError):
    pass


def dying(data, after):
    yield data[:after]
    raise BoomError("source died")


def test_put_failing_after_batches_leaves_nothing(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    try:
        bid = new_id()
        with pytest.raises(BoomError):
            backend.put(dying(pattern(5000), 1050), blob_id=bid)  # three batches landed
        assert not backend.exists(bid)
        assert chunk_count(backend, bid) == 0
        assert leftovers(backend) == []
        assert backend.put(b"again", blob_id=bid).id == bid
    finally:
        backend.close()


async def test_cancelled_aput_after_batches_leaves_nothing(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    landed = asyncio.Event()

    async def slow():
        yield pattern(1050)
        landed.set()
        await asyncio.sleep(60)

    try:
        task = asyncio.ensure_future(backend.aput(slow()))
        await landed.wait()
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert leftovers(backend) == []
        with backend._env.begin() as txn:
            assert txn.stat(backend._data)["entries"] == 0
    finally:
        backend.close()


def dead_pid():
    child = multiprocessing.get_context("spawn").Process(target=abs, args=(0,))
    child.start()
    child.join(timeout=30)
    return child.pid


def plant_dead_put(backend, blob_id, chunks=3):
    """What a process killed mid-put leaves: chunks and a claim, no meta."""
    raw = bytes.fromhex(blob_id)
    claim = json.dumps({"pid": dead_pid(), "token": "t"}).encode()
    with backend._env.begin(write=True) as txn:
        txn.put(blob_id.encode(), claim, db=backend._claims)
        for index in range(chunks):
            txn.put(raw + index.to_bytes(8, "big"), b"x" * 100, db=backend._data)


def test_open_sweeps_a_dead_put(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    kept = backend.put(pattern(1000)).id
    bid = new_id()
    plant_dead_put(backend, bid)
    assert leftovers(backend) == [bid]
    backend.close()
    backend.open()  # the first open in the process sweeps
    try:
        assert leftovers(backend) == []
        assert backend.read(kept) == pattern(1000)
    finally:
        backend.close()


def test_put_takes_over_a_dead_put(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    try:
        bid = new_id()
        plant_dead_put(backend, bid, chunks=20)
        backend.put(pattern(250), blob_id=bid)  # fewer chunks than the dead put left
        assert backend.read(bid) == pattern(250)
        assert chunk_count(backend, bid) == 3
        assert leftovers(backend) == []
    finally:
        backend.close()


def test_delete_clears_a_dead_put(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    try:
        bid = new_id()
        plant_dead_put(backend, bid)
        assert backend.delete(bid) is False  # no blob was there
        assert leftovers(backend) == []
    finally:
        backend.close()


def test_live_put_holds_its_id(tmp_path):
    backend = chunked(tmp_path, 100, 300)
    bid = new_id()
    landed, go = threading.Event(), threading.Event()

    def held():
        yield pattern(1050)
        landed.set()
        go.wait(10)
        yield pattern(2000)[1050:]

    result = []
    writer = threading.Thread(target=lambda: result.append(backend.put(held(), blob_id=bid)))
    writer.start()
    try:
        assert landed.wait(10)
        with pytest.raises(BlobExists):
            backend.put(b"other", blob_id=bid)
        with pytest.raises(BlobExists):
            backend.put(iter([b"x" * 1000]), blob_id=bid)
        assert backend.delete(bid) is False  # a live put is left alone
        assert not backend.exists(bid)
        go.set()
        writer.join(10)
        assert backend.read(bid) == pattern(2000)
        assert leftovers(backend) == []
    finally:
        go.set()
        writer.join(10)
        backend.close()


@pytest.mark.timeout(120)
def test_killed_process_mid_put_is_swept(tmp_path):
    path = tmp_path / "env"
    ctx = multiprocessing.get_context("spawn")
    ready, go = ctx.Queue(), ctx.Queue()
    child = ctx.Process(target=stalled_putter, args=(str(path), CONTESTED, ready, go))
    child.start()
    try:
        assert ready.get(timeout=60) == "stalled"
        os.kill(child.pid, signal.SIGKILL)
    finally:
        child.join(timeout=30)
    backend = LMDBBackend(path)
    backend.open()
    try:
        assert not backend.exists(CONTESTED)
        assert leftovers(backend) == []
        with backend._env.begin() as txn:
            assert txn.stat(backend._data)["entries"] == 0
    finally:
        backend.close()


@pytest.mark.timeout(120)
def test_two_processes_race_one_id_over_many_batches(tmp_path):
    path = tmp_path / "env"
    setup = LMDBBackend(path)
    setup.open()
    setup.close()
    ctx = multiprocessing.get_context("spawn")
    barrier = ctx.Barrier(2)
    out = ctx.Queue()
    children = [ctx.Process(target=racer, args=(str(path), me, barrier, out)) for me in (0, 1)]
    for child in children:
        child.start()
    results = [out.get(timeout=60) for _ in children]
    for child in children:
        child.join(timeout=30)
        assert child.exitcode == 0
    assert sorted(won for _, won in results) == [False, True]
    winner = next(worker for worker, won in results if won)
    backend = LMDBBackend(path)
    backend.open()
    try:
        assert backend.read(CONTESTED) == race_content(winner)
        assert leftovers(backend) == []
    finally:
        backend.close()


# ---- past the old 2 GiB cap ----------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "darwin", reason="writes 2 GiB: red only")
def test_blob_past_two_gib(tmp_path):
    size = (2 << 30) + (3 << 20) + 7
    marks = {0: b"head", (1 << 31) - 2: b"edge", size - 4: b"tail"}
    source = tmp_path / "huge.bin"
    with source.open("wb") as file:
        file.truncate(size)  # sparse: zeros, no disk behind them
        for offset, mark in marks.items():
            file.seek(offset)
            file.write(mark)
    backend = LMDBBackend(tmp_path / "env")
    backend.open()
    try:
        info = backend.put(source)
        source.unlink()
        assert info.size == size
        for offset, mark in marks.items():
            assert backend.read(info.id, offset, offset + len(mark)) == mark
        tail = b"".join(backend.stream(info.id, size - (5 << 20), step=1 << 20))
        assert len(tail) == 5 << 20
        assert tail.endswith(b"tail")
        assert backend.delete(info.id)
    finally:
        backend.close()
