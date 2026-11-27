"""Compliance suite every blob backend passes (parametrized in conftest)."""

from __future__ import annotations

import array
import asyncio
import io
import threading
import time

import pytest
from _support.blob_fixtures import leftovers

from nustd.blob import (
    BlobBackend,
    BlobExists,
    BlobInfo,
    BlobNotFound,
    BlobTooLarge,
)
from nustd.blob._base import check_id, clamp, new_id


DATA = bytes(range(256)) * 40  # 10240 bytes, every offset distinct mod 256


class BoomError(RuntimeError):
    pass


def failing(pieces=3):
    for _ in range(pieces):
        yield b"x" * 1000
    raise BoomError("source died")


async def afailing(pieces=3):
    for _ in range(pieces):
        yield b"x" * 1000
        await asyncio.sleep(0)
    raise BoomError("source died")


async def agen(*pieces):
    for piece in pieces:
        await asyncio.sleep(0)
        yield piece


def pending_uploads(backend):
    listing = backend._client.list_multipart_uploads(Bucket=backend.bucket, Prefix=backend.prefix)
    return sorted(upload["Key"] for upload in listing.get("Uploads", []))


def stored_ids(kind, backend):
    """Every id the store holds any bytes for, visible or not."""
    if kind == "s3":
        listing = backend._client.list_objects_v2(Bucket=backend.bucket, Prefix=backend.prefix)
        keys = [item["Key"] for item in listing.get("Contents", [])] + pending_uploads(backend)
        return sorted(key[len(backend.prefix) :] for key in keys)
    if kind == "files":
        return sorted(p.name for p in (backend.root / "blobs").glob("*/*") if p.suffix != ".json")
    with backend._env.begin() as txn:
        chunked = {k[:16].hex() for k, _ in txn.cursor(db=backend._data)}
        claimed = {k.decode() for k, _ in txn.cursor(db=backend._claims)}
        return sorted(chunked | claimed)


# ---- the protocol --------------------------------------------------------------------------


def test_is_a_blob_backend(backend):
    assert isinstance(backend, BlobBackend)


def test_info_round_trips():
    info = BlobInfo(id=new_id(), size=3, mime="a/b", name="n", created_at=1.5)
    assert BlobInfo.from_dict(info.to_dict()) == info


def test_clamp():
    assert clamp(0, None, 10) == (0, 10)
    assert clamp(2, 5, 10) == (2, 5)
    assert clamp(8, 20, 10) == (8, 10)
    assert clamp(20, None, 10) == (10, 10)
    assert clamp(5, 3, 10) == (5, 5)


@pytest.mark.parametrize(
    "bad",
    ["", "A" * 32, "a" * 31, "a" * 33, "../" + "a" * 29, "g" * 32, "a" * 31 + "\n", 7, None],
)
def test_check_id_refuses(bad):
    with pytest.raises(ValueError, match="32 lowercase hex"):
        check_id(bad)


# ---- put sources ---------------------------------------------------------------------------


def test_put_bytes_mints_an_id(backend):
    info = backend.put(DATA, mime="application/octet-stream", name="d.bin")
    assert check_id(info.id) == info.id
    assert info.size == len(DATA)
    assert (info.mime, info.name) == ("application/octet-stream", "d.bin")
    assert abs(info.created_at - time.time()) < 60
    assert backend.read(info.id) == DATA


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda: bytearray(DATA), id="bytearray"),
        pytest.param(lambda: memoryview(DATA), id="memoryview"),
        pytest.param(lambda: memoryview(DATA)[100:5100], id="memoryview-slice"),
        pytest.param(lambda: io.BytesIO(DATA), id="file"),
        pytest.param(lambda: [DATA[:100], DATA[100:]], id="list"),
        pytest.param(lambda: (DATA[i : i + 999] for i in range(0, len(DATA), 999)), id="generator"),
        pytest.param(
            lambda: iter([memoryview(DATA[:10]), bytearray(DATA[10:])]), id="mixed-pieces"
        ),
    ],
)
def test_put_sources(backend, make_source):
    source = make_source()
    expected = bytes(source) if isinstance(source, (bytearray, memoryview)) else DATA
    info = backend.put(source)
    assert info.size == len(expected)
    assert backend.read(info.id) == expected
    assert leftovers(backend) == []


def test_put_typed_memoryview_counts_bytes(backend):
    numbers = array.array("i", range(100))
    info = backend.put(memoryview(numbers))
    assert info.size == numbers.itemsize * 100
    assert backend.read(info.id) == numbers.tobytes()


def test_put_path(backend, tmp_path):
    source = tmp_path / "src.bin"
    source.write_bytes(DATA)
    info = backend.put(source, mime="x/y")
    assert backend.read(info.id) == DATA
    assert source.read_bytes() == DATA


def test_put_real_file(backend, tmp_path):
    source = tmp_path / "src.bin"
    source.write_bytes(DATA)
    with source.open("rb") as file:
        info = backend.put(file)
    assert backend.read(info.id) == DATA


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda tmp: b"", id="bytes"),
        pytest.param(lambda tmp: [], id="iterable"),
        pytest.param(lambda tmp: io.BytesIO(), id="file"),
        pytest.param(lambda tmp: (tmp / "empty").touch() or (tmp / "empty"), id="path"),
    ],
)
def test_put_empty(backend, tmp_path, make_source):
    info = backend.put(make_source(tmp_path))
    assert info.size == 0
    assert backend.exists(info.id)
    assert backend.read(info.id) == b""
    assert list(backend.stream(info.id)) == []


def test_put_given_id(backend):
    bid = new_id()
    assert backend.put(DATA, blob_id=bid).id == bid
    assert backend.read(bid) == DATA


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("some text", id="str"),
        pytest.param(42, id="int"),
        pytest.param(agen(b"a"), id="async-iterable"),
    ],
)
def test_put_refuses(backend, source):
    with pytest.raises(TypeError):
        backend.put(source)
    if hasattr(source, "aclose"):
        asyncio.run(source.aclose())


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda: [b"ok", "text"], id="str-piece"),
        pytest.param(lambda: [b"ok", 5], id="int-piece"),
        pytest.param(lambda: io.StringIO("text"), id="text-file"),
        pytest.param(lambda: io.StringIO(""), id="empty-text-file"),
    ],
)
def test_put_refuses_pieces_and_leaves_nothing(kind, backend, make_source):
    with pytest.raises(TypeError):
        backend.put(make_source())
    assert leftovers(backend) == []
    assert stored_ids(kind, backend) == []


@pytest.mark.parametrize("bad", ["NOTHEX", "../../etc/passwd", "a" * 31])
def test_put_refuses_bad_id(backend, bad):
    with pytest.raises(ValueError):
        backend.put(DATA, blob_id=bad)


# ---- write-once ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda: b"other", id="bytes"),
        pytest.param(lambda: iter([b"other"]), id="iterable"),
    ],
)
def test_write_once(backend, make_source):
    info = backend.put(DATA)
    with pytest.raises(BlobExists):
        backend.put(make_source(), blob_id=info.id)
    assert backend.read(info.id) == DATA
    assert leftovers(backend) == []


def test_write_once_holds_without_the_precheck(backend, monkeypatch):
    # The pre-check is only a shortcut; the store itself refuses a taken id.
    info = backend.put(DATA)
    monkeypatch.setattr(backend, "exists", lambda blob_id: False)
    with pytest.raises(BlobExists):
        backend.put(iter([b"other"]), blob_id=info.id)
    with pytest.raises(BlobExists):
        backend.put(b"other", blob_id=info.id)
    assert backend.read(info.id) == DATA
    assert leftovers(backend) == []


def test_write_once_holds_without_the_precheck_path(backend, tmp_path, monkeypatch):
    source = tmp_path / "src.bin"
    source.write_bytes(b"other")
    info = backend.put(DATA)
    monkeypatch.setattr(backend, "exists", lambda blob_id: False)
    with pytest.raises(BlobExists):
        backend.put(source, blob_id=info.id)
    assert backend.read(info.id) == DATA
    assert leftovers(backend) == []


# ---- whole or nothing ----------------------------------------------------------------------


def test_failing_iterable_leaves_nothing(kind, backend):
    bid = new_id()
    with pytest.raises(BoomError):
        backend.put(failing(), blob_id=bid)
    assert not backend.exists(bid)
    with pytest.raises(BlobNotFound):
        backend.info(bid)
    assert leftovers(backend) == []
    assert stored_ids(kind, backend) == []
    assert backend.put(DATA, blob_id=bid).id == bid  # the id is still free


async def test_failing_async_iterable_leaves_nothing(kind, backend):
    bid = new_id()
    with pytest.raises(BoomError):
        await backend.aput(afailing(), blob_id=bid)
    assert not await backend.aexists(bid)
    assert leftovers(backend) == []
    assert stored_ids(kind, backend) == []


def test_too_large_iterable_stops_early(kind, backend, monkeypatch):
    monkeypatch.setattr(backend, "max_size", 2500, raising=False)
    pulled = []

    def pieces():
        for index in range(100):
            pulled.append(index)
            yield b"x" * 1000

    with pytest.raises(BlobTooLarge):
        backend.put(pieces())
    assert len(pulled) == 3
    assert leftovers(backend) == []
    assert stored_ids(kind, backend) == []


async def test_too_large_async_iterable_stops_early(kind, backend, monkeypatch):
    monkeypatch.setattr(backend, "max_size", 2500, raising=False)
    with pytest.raises(BlobTooLarge):
        await backend.aput(agen(*[b"x" * 1000] * 10))
    assert leftovers(backend) == []
    assert stored_ids(kind, backend) == []


# ---- info / exists / read / stream / delete ------------------------------------------------


def test_info_and_exists(backend):
    info = backend.put(DATA, mime="image/png", name="cat.png")
    assert backend.exists(info.id)
    assert backend.info(info.id) == info
    other = new_id()
    assert not backend.exists(other)
    with pytest.raises(BlobNotFound):
        backend.info(other)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (0, None, DATA),
        (2, 5, DATA[2:5]),
        (100, None, DATA[100:]),
        (0, 100, DATA[:100]),
        (len(DATA) - 3, len(DATA) + 1000, DATA[-3:]),
        (len(DATA), None, b""),
        (len(DATA) + 50, None, b""),
        (50, 50, b""),
        (60, 50, b""),
    ],
)
def test_read_ranges(backend, start, end, expected):
    info = backend.put(DATA)
    assert backend.read(info.id, start, end) == expected
    assert b"".join(backend.stream(info.id, start, end, step=7)) == expected


@pytest.mark.parametrize(("start", "end"), [(-1, None), (0, -1)])
def test_negative_range_refused(backend, start, end):
    info = backend.put(DATA)
    with pytest.raises(ValueError):
        backend.read(info.id, start, end)
    with pytest.raises(ValueError):
        backend.stream(info.id, start, end)


def test_stream_pieces(backend):
    info = backend.put(DATA)
    pieces = list(backend.stream(info.id, 10, 2010, step=500))
    assert [len(p) for p in pieces] == [500, 500, 500, 500]
    assert b"".join(pieces) == DATA[10:2010]
    assert all(type(p) is bytes for p in pieces)


def test_stream_default_step(backend):
    info = backend.put(bytes(3 << 20))
    assert [len(p) for p in backend.stream(info.id)] == [1 << 20] * 3


def test_stream_refuses_bad_step(backend):
    info = backend.put(DATA)
    with pytest.raises(ValueError):
        backend.stream(info.id, step=0)


def test_stream_missing_raises_at_first_pull(backend):
    pieces = backend.stream(new_id())  # no error yet
    with pytest.raises(BlobNotFound):
        next(pieces)


def test_stream_missing_empty_range_still_raises(backend):
    with pytest.raises(BlobNotFound):
        list(backend.stream(new_id(), 5, 5))


def test_read_missing(backend):
    with pytest.raises(BlobNotFound):
        backend.read(new_id())


def test_delete(backend):
    info = backend.put(DATA)
    assert backend.delete(info.id) is True
    assert not backend.exists(info.id)
    with pytest.raises(BlobNotFound):
        backend.read(info.id)
    assert backend.delete(info.id) is False


def test_delete_leaves_others(backend):
    keep = backend.put(b"keep")
    gone = backend.put(b"gone")
    backend.delete(gone.id)
    assert backend.read(keep.id) == b"keep"


@pytest.mark.parametrize("call", ["info", "exists", "read", "stream", "delete"])
def test_bad_id_refused_everywhere(backend, call):
    with pytest.raises(ValueError):
        getattr(backend, call)("../" + "a" * 29)


# ---- async twins ---------------------------------------------------------------------------


async def test_async_twins(backend, tmp_path):
    source = tmp_path / "src.bin"
    source.write_bytes(DATA)
    from_path = await backend.aput(source, mime="x/y")
    from_bytes = await backend.aput(DATA)
    from_iter = await backend.aput(iter([DATA[:5], DATA[5:]]))
    from_async = await backend.aput(agen(DATA[:5000], DATA[5000:]), name="a")
    for info in (from_path, from_bytes, from_iter, from_async):
        assert await backend.aexists(info.id)
        assert await backend.aread(info.id) == DATA
        assert await backend.aread(info.id, 3, 9) == DATA[3:9]
        assert (await backend.ainfo(info.id)).size == len(DATA)
    assert (await backend.ainfo(from_async.id)).name == "a"
    pieces = [p async for p in backend.astream(from_async.id, 1, 3001, step=1000)]
    assert [len(p) for p in pieces] == [1000, 1000, 1000]
    assert b"".join(pieces) == DATA[1:3001]
    assert await backend.adelete(from_async.id) is True
    assert not await backend.aexists(from_async.id)
    assert leftovers(backend) == []


async def test_aput_async_iterable_given_id_and_write_once(backend):
    bid = new_id()
    assert (await backend.aput(agen(b"a", b"b"), blob_id=bid)).id == bid
    with pytest.raises(BlobExists):
        await backend.aput(agen(b"c"), blob_id=bid)
    assert await backend.aread(bid) == b"ab"


async def test_aput_refuses(backend):
    with pytest.raises(TypeError):
        await backend.aput("text")
    with pytest.raises(ValueError):
        await backend.aput(agen(b"a"), blob_id="nope")
    with pytest.raises(TypeError):
        await backend.aput(agen(b"ok", "text"))
    assert leftovers(backend) == []


async def test_astream_missing(backend):
    with pytest.raises(BlobNotFound):
        async for _ in backend.astream(new_id()):
            pass
    with pytest.raises(BlobNotFound):
        await backend.aread(new_id())
    with pytest.raises(BlobNotFound):
        await backend.ainfo(new_id())


async def test_astream_stops_early(backend):
    info = backend.put(DATA)
    pieces = backend.astream(info.id, step=100)
    assert await pieces.__anext__() == DATA[:100]
    await pieces.aclose()


async def test_concurrent_async_puts(backend):
    infos = await asyncio.gather(*(backend.aput(agen(bytes([i]) * 5000)) for i in range(20)))
    for i, info in enumerate(infos):
        assert await backend.aread(info.id) == bytes([i]) * 5000


@pytest.mark.timeout(60)
async def test_concurrent_async_puts_same_id(backend):
    # Every loser aborts its write; in LMDB that must not hang the waiting writers.
    bid = new_id()
    results = await asyncio.wait_for(
        asyncio.gather(
            *(backend.aput(agen(bytes([i]) * 5000), blob_id=bid) for i in range(8)),
            return_exceptions=True,
        ),
        timeout=30,
    )
    wins = [r for r in results if isinstance(r, BlobInfo)]
    assert len(wins) == 1
    assert all(isinstance(r, BlobExists) for r in results if r not in wins)
    value = await backend.aread(bid)
    assert value == value[:1] * 5000


@pytest.mark.timeout(60)
def test_threads_mix_losing_puts_with_writers(backend, monkeypatch):
    # The store's own guard decides, so each loser aborts inside the write.
    monkeypatch.setattr(backend, "exists", lambda blob_id: False)
    bid = new_id()
    won, lost, others = [], [], []

    def contend(i):
        try:
            won.append(backend.put(bytes([i]) * 1000, blob_id=bid))
        except BlobExists:
            lost.append(i)

    def write(i):
        info = backend.put(bytes([i]) * 1000)
        if i % 3 == 0:
            backend.delete(info.id)
        else:
            others.append(info)

    threads = [threading.Thread(target=contend if i % 2 else write, args=(i,)) for i in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    assert len(won) == 1
    assert len(lost) == 19
    for info in others:
        value = backend.read(info.id)
        assert value == value[:1] * 1000
