"""What only the s3 backend does: multipart puts, conditional writes, metadata, flat memory.

Every S3 call runs on moto (``moto_s3`` in conftest), except the memory tests:
moto keeps each byte it is sent in this process and joins the parts whole on
complete, so a tracemalloc peak over moto measures moto. Those run a real
boto3 client whose sends are drained piece by piece and answered locally, so
the peak is the backend's and botocore's own.
"""

from __future__ import annotations

import asyncio
import io
import threading
import time
import tracemalloc

import boto3
import pytest
from _support.blob_workers import BUCKET
from botocore.awsrequest import AWSResponse
from botocore.exceptions import ClientError

from nustd.blob import BlobExists, BlobNotFound, BlobTooLarge, S3Backend
from nustd.blob._base import new_id
from nustd.blob.backends.s3 import DEFAULT_PART_SIZE, MAX_PARTS, MIN_PART_SIZE


PART = MIN_PART_SIZE
SIZE = 2 * PART + 1234  # three parts, the last one short


def pattern(size):
    return bytes(range(251)) * (size // 251) + bytes(range(size % 251))


DATA = pattern(SIZE)


def pieces(data=DATA, step=1 << 20):
    for offset in range(0, len(data), step):
        yield data[offset : offset + step]


async def apieces(data=DATA, step=1 << 20):
    for piece in pieces(data, step):
        await asyncio.sleep(0)
        yield piece


class BoomError(RuntimeError):
    pass


def dying(after):
    yield from pieces(DATA[:after])
    raise BoomError("source died")


@pytest.fixture
def s3(moto_s3):
    backend = S3Backend(BUCKET, prefix="t/", part_size=PART)
    backend.open()
    yield backend
    backend.close()


def head(backend, blob_id):
    return backend._client.head_object(Bucket=BUCKET, Key=f"t/{blob_id}")


def pending(backend):
    return backend._client.list_multipart_uploads(Bucket=BUCKET).get("Uploads", [])


def keys(backend):
    listing = backend._client.list_objects_v2(Bucket=BUCKET)
    return [item["Key"] for item in listing.get("Contents", [])]


def parts_of(backend, blob_id):
    """How many parts the object went up in; 0 for a single PutObject."""
    etag = head(backend, blob_id)["ETag"].strip('"')
    return int(etag.split("-")[1]) if "-" in etag else 0


# ---- multipart ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda tmp: pieces(), id="iterable"),
        pytest.param(lambda tmp: io.BytesIO(DATA), id="file"),
        pytest.param(lambda tmp: (tmp / "src").write_bytes(DATA) and tmp / "src", id="path"),
        pytest.param(lambda tmp: DATA, id="bytes"),
        pytest.param(lambda tmp: memoryview(bytearray(DATA)), id="memoryview"),
    ],
)
def test_big_put_goes_multipart(s3, tmp_path, make_source):
    info = s3.put(make_source(tmp_path), mime="video/mp4", name="v.mp4")
    assert info.size == SIZE
    assert parts_of(s3, info.id) == 3
    assert s3.read(info.id) == DATA
    assert s3.info(info.id) == info
    edge = PART - 3
    assert s3.read(info.id, edge, edge + 10) == DATA[edge : edge + 10]
    assert b"".join(s3.stream(info.id, edge, SIZE - 5, step=PART)) == DATA[edge : SIZE - 5]
    assert pending(s3) == []


def test_one_part_is_one_put_object(s3):
    info = s3.put(pieces(DATA[:PART]))
    assert parts_of(s3, info.id) == 0
    assert s3.read(info.id) == DATA[:PART]


def test_exactly_two_parts(s3):
    info = s3.put(pieces(DATA[: 2 * PART]))
    assert parts_of(s3, info.id) == 2
    assert s3.read(info.id) == DATA[: 2 * PART]


async def test_async_iterable_goes_multipart(s3):
    info = await s3.aput(apieces(), name="a")
    assert parts_of(s3, info.id) == 3
    assert await s3.aread(info.id) == DATA
    assert pending(s3) == []


# ---- whole or nothing ------------------------------------------------------------------------


def test_failure_after_parts_aborts_the_upload(s3):
    bid = new_id()
    with pytest.raises(BoomError):
        s3.put(dying(PART + 100), blob_id=bid)  # one part sent, the second filling
    assert pending(s3) == []
    assert keys(s3) == []
    assert not s3.exists(bid)
    assert s3.put(b"x", blob_id=bid).id == bid  # the id is still free


async def test_async_failure_after_parts_aborts_the_upload(s3):
    async def adying():
        async for piece in apieces(DATA[: PART + 100]):
            yield piece
        raise BoomError("source died")

    with pytest.raises(BoomError):
        await s3.aput(adying())
    assert pending(s3) == []
    assert keys(s3) == []


async def test_cancelled_aput_aborts_the_upload(s3):
    started = asyncio.Event()

    async def slow():
        async for piece in apieces(DATA[: PART + 100]):
            yield piece
        started.set()
        await asyncio.sleep(60)

    task = asyncio.ensure_future(s3.aput(slow()))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert pending(s3) == []
    assert keys(s3) == []


async def test_cancel_while_the_upload_is_being_created_still_aborts_it(s3, monkeypatch):
    # The abort must wait for the creation in flight, or it finds no upload to abort.
    in_flight = threading.Event()
    create = s3._client.create_multipart_upload

    def slow_create(**kw):
        in_flight.set()
        time.sleep(0.3)
        return create(**kw)

    monkeypatch.setattr(s3._client, "create_multipart_upload", slow_create)

    async def endless():
        while True:
            yield b"x" * (1 << 20)
            await asyncio.sleep(0)

    task = asyncio.ensure_future(s3.aput(endless()))
    while not in_flight.is_set():
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(0.5)  # past the slow creation, had the put not waited for it
    assert pending(s3) == []
    assert keys(s3) == []


def test_too_large_stops_mid_upload_and_aborts(s3, monkeypatch):
    monkeypatch.setattr(s3, "max_size", PART + 10)
    with pytest.raises(BlobTooLarge):
        s3.put(pieces())
    assert pending(s3) == []
    assert keys(s3) == []


@pytest.mark.parametrize("source", ["bytes", "path"])
def test_too_large_known_size_sends_nothing(s3, tmp_path, monkeypatch, source):
    monkeypatch.setattr(s3, "max_size", 100)
    calls = []
    monkeypatch.setattr(s3._client, "put_object", lambda **kw: calls.append(kw))
    monkeypatch.setattr(s3._client, "create_multipart_upload", lambda **kw: calls.append(kw))
    src = b"x" * 101
    if source == "path":
        (tmp_path / "src").write_bytes(src)
        src = tmp_path / "src"
    with pytest.raises(BlobTooLarge):
        s3.put(src)
    assert calls == []


def test_max_size_follows_part_size():
    assert S3Backend("b", part_size=PART).max_size == PART * MAX_PARTS
    assert S3Backend("b").max_size == DEFAULT_PART_SIZE * MAX_PARTS
    assert S3Backend("b", part_size=5 << 30).max_size == 5 << 40  # S3's 5 TiB cap


@pytest.mark.parametrize("size", [PART - 1, (5 << 30) + 1])
def test_part_size_bounds(size):
    with pytest.raises(ValueError, match="part_size"):
        S3Backend("b", part_size=size)


# ---- write-once ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_source",
    [
        pytest.param(lambda: b"other", id="put-object"),
        pytest.param(lambda: pieces(), id="multipart"),
    ],
)
def test_conditional_write_refuses_a_taken_id(s3, monkeypatch, make_source):
    # No pre-check: the refusal is S3's own, If-None-Match on the write.
    info = s3.put(b"first")
    monkeypatch.setattr(s3, "exists", lambda blob_id: False)
    with pytest.raises(BlobExists):
        s3.put(make_source(), blob_id=info.id)
    assert s3.read(info.id) == b"first"
    assert pending(s3) == []


def test_every_write_is_conditional(s3, monkeypatch):
    seen = []
    client = s3._client
    for name in ("put_object", "complete_multipart_upload"):
        call = getattr(client, name)
        monkeypatch.setattr(
            client,
            name,
            lambda _call=call, _name=name, **kw: seen.append((_name, kw)) or _call(**kw),
        )
    s3.put(b"small")
    s3.put(pieces())
    assert [name for name, _ in seen] == ["put_object", "complete_multipart_upload"]
    assert all(kw["IfNoneMatch"] == "*" for _, kw in seen)


def test_conditional_conflict_is_retried(s3, monkeypatch):
    # S3 answers 409 when a concurrent conditional write on the key is in flight.
    call = s3._client.put_object
    tries = []

    def flaky(**kw):
        tries.append(1)
        if len(tries) == 1:
            # S3 answers 409 after it took the body: the retry must send it again.
            assert kw["Body"].read() == b"data"
            raise ClientError(
                {"Error": {"Code": "ConditionalRequestConflict", "Message": "busy"}}, "PutObject"
            )
        return call(**kw)

    monkeypatch.setattr(s3._client, "put_object", flaky)
    info = s3.put(b"data")
    assert len(tries) == 2
    assert s3.read(info.id) == b"data"
    assert s3.info(info.id).size == 4


# ---- metadata --------------------------------------------------------------------------------


def test_non_ascii_name_and_mime_round_trip(s3):
    info = s3.put(b"meow", mime="image/png", name="кот 🐱 %20.png")
    assert s3.info(info.id) == info
    raw = head(s3, info.id)
    assert raw["ContentType"] == "image/png"
    assert all(value.isascii() for value in raw["Metadata"].values())


@pytest.mark.parametrize("name", ["к" * 400, "a" * 2100])
def test_metadata_over_the_cap_is_refused_before_any_request(s3, monkeypatch, name):
    calls = []
    monkeypatch.setattr(s3._client, "_make_api_call", lambda *a, **kw: calls.append(a))
    with pytest.raises(ValueError, match="metadata"):
        s3.put(b"x", name=name)
    with pytest.raises(ValueError, match="metadata"):
        asyncio.run(s3.aput(_agen(b"x"), name=name))
    assert calls == []


def test_metadata_under_the_cap_goes_through(s3):
    info = s3.put(b"x", name="к" * 300)
    assert s3.info(info.id).name == "к" * 300


async def _agen(*pieces):
    for piece in pieces:
        yield piece


def test_empty_mime_round_trips(s3):
    info = s3.put(b"x")
    assert s3.info(info.id).mime == ""


def test_object_put_by_another_client_reads_its_own_headers(s3):
    bid = new_id()
    s3._client.put_object(Bucket=BUCKET, Key=f"t/{bid}", Body=b"abc", ContentType="text/plain")
    info = s3.info(bid)
    assert (info.size, info.mime, info.name) == (3, "text/plain", "")
    assert info.created_at == head(s3, bid)["LastModified"].timestamp()


def test_prefix_keeps_stores_apart(moto_s3):
    a = S3Backend(BUCKET, prefix="a/")
    b = S3Backend(BUCKET, prefix="b/")
    a.open()
    b.open()
    info = a.put(b"in a")
    assert not b.exists(info.id)
    assert keys(a) == [f"a/{info.id}"]


# ---- reads -----------------------------------------------------------------------------------


def test_stream_is_one_ranged_get_per_piece(s3, monkeypatch):
    info = s3.put(DATA[:10_000])
    ranges = []
    call = s3._client.get_object
    monkeypatch.setattr(
        s3._client, "get_object", lambda **kw: ranges.append(kw.get("Range")) or call(**kw)
    )
    pieces = s3.stream(info.id, 100, 3100, step=1000)
    assert ranges == []
    assert next(pieces) == DATA[100:1100]
    assert ranges == ["bytes=100-1099"]
    assert b"".join(pieces) == DATA[1100:3100]
    assert ranges == ["bytes=100-1099", "bytes=1100-2099", "bytes=2100-3099"]


def test_stream_of_a_blob_replaced_mid_way_raises(s3):
    info = s3.put(DATA[:3000])
    pieces = s3.stream(info.id, step=1000)
    assert next(pieces) == DATA[:1000]
    s3.delete(info.id)
    s3.put(b"y" * 3000, blob_id=info.id)
    with pytest.raises(BlobNotFound):
        next(pieces)


def test_read_past_the_end_of_an_empty_blob(s3):
    info = s3.put(b"")
    assert s3.read(info.id, 0, 10) == b""
    assert s3.read(info.id, 5) == b""


def test_delete_of_a_missing_blob_sends_no_delete(s3, monkeypatch):
    calls = []
    monkeypatch.setattr(s3._client, "delete_object", lambda **kw: calls.append(kw))
    assert s3.delete(new_id()) is False
    assert calls == []


# ---- memory ----------------------------------------------------------------------------------


BIG = 64 << 20
STEP = 1 << 20


class _Raw(io.BytesIO):
    def stream(self, **_):
        yield self.getvalue()


_REPLIES = {
    "CreateMultipartUpload": (
        b"<InitiateMultipartUploadResult><Bucket>b</Bucket><Key>k</Key>"
        b"<UploadId>u</UploadId></InitiateMultipartUploadResult>"
    ),
    "CompleteMultipartUpload": (
        b"<CompleteMultipartUploadResult><Bucket>b</Bucket><Key>k</Key>"
        b'<ETag>"e-1"</ETag></CompleteMultipartUploadResult>'
    ),
}


@pytest.fixture
def sink():
    """An s3 backend on a real boto3 client whose requests go nowhere.

    Each request body is drained 64 KiB at a time, as a socket would, and
    its payload counted; the reply is made up locally.
    """
    received = []
    client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="x",
        aws_secret_access_key="x",  # noqa: S106 (a sink, no service behind it)
    )

    def reply(request, event_name, **_):
        body, size = request.body, 0
        if hasattr(body, "read"):
            while chunk := body.read(1 << 16):
                size += len(chunk)
        elif body:
            size = len(body)
        # botocore sends parts aws-chunked with a checksum trailer; count the payload.
        size = int(request.headers.get("x-amz-decoded-content-length", size))
        operation = event_name.rsplit(".", 1)[-1]
        received.append((operation, size))
        content = _REPLIES.get(operation, b"")
        return AWSResponse(request.url, 200, {"ETag": '"e"'}, _Raw(content))

    client.meta.events.register("before-send.s3", reply)
    backend = S3Backend(BUCKET, part_size=PART)
    backend._client = client
    backend._error = ClientError
    yield backend, received
    client.close()


def big_pieces():
    for index in range(BIG // STEP):
        yield bytes([index % 256]) * STEP


async def abig_pieces():
    for piece in big_pieces():
        yield piece


def check_sent(received):
    parts = [size for operation, size in received if operation == "UploadPart"]
    assert sum(parts) == BIG
    assert parts[:-1] == [PART] * (len(parts) - 1)
    assert received[-1][0] == "CompleteMultipartUpload"


def test_iterable_put_peak_is_one_part(sink):
    backend, received = sink
    tracemalloc.start()
    try:
        info = backend.put(big_pieces())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert info.size == BIG
    check_sent(received)
    assert peak < 2 * PART, f"peak {peak} for a {BIG} byte put, parts of {PART}"


async def test_async_iterable_put_peak_is_one_part(sink):
    backend, received = sink
    tracemalloc.start()
    try:
        info = await backend.aput(abig_pieces())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert info.size == BIG
    check_sent(received)
    assert peak < 2 * PART, f"peak {peak} for a {BIG} byte put, parts of {PART}"


def test_path_put_peak_is_one_part(sink, tmp_path):
    backend, received = sink
    source = tmp_path / "big"
    with source.open("wb") as out:
        for piece in big_pieces():
            out.write(piece)
    tracemalloc.start()
    try:
        backend.put(source)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    check_sent(received)
    assert peak < 2 * PART, f"peak {peak} for a {BIG} byte put, parts of {PART}"
