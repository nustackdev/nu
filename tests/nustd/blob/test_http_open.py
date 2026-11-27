"""Open blobs over HTTP: a GET follows a blob as it grows, a POST is readable while it uploads.

Local backends only (s3 holds no open blobs), each with small batches, so a
put spans many commits.
"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest
from _support.blob_workers import LOCAL_KINDS, make_small
from starlette.applications import Starlette
from starlette.testclient import TestClient

from nustd.blob import BlobIdle
from nustd.blob.http import BlobMount
from nustd.blob.http.serving import OPEN_CACHE_CONTROL, routes


DATA = bytes(range(251)) * 40  # 10040 bytes
AT = "/media"
MEDIA = BlobMount(AT)


@pytest.fixture(params=LOCAL_KINDS)
def local(request):
    return request.param


@pytest.fixture
def store(local, store_path):
    backend = make_small(local, store_path)
    backend.open()
    yield backend
    backend.close()


def app_of(store, **options):
    return Starlette(routes=routes(MEDIA, store, **options))


@pytest.fixture
def client(store):
    with TestClient(app_of(store)) as client:
        yield client


def url(blob_id):
    return f"{AT}/{blob_id}"


def later(delay, call, *args):
    def run():
        time.sleep(delay)
        call(*args)

    thread = threading.Thread(target=run)
    thread.start()
    return thread


def stored_ids(store):
    """Every id with a meta in the store, open or sealed."""
    if hasattr(store, "root"):
        return [p.stem for p in (store.root / "blobs").glob("*/*.json")]
    with store._env.begin() as txn:
        return [bytes(key).decode() for key, _ in txn.cursor(db=store._meta)]


async def drive(app, method, path, headers=(), receive=None, on_send=None):
    """Drive one request over raw ASGI; every message sent, in order."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(k.encode(), v.encode()) for k, v in headers],
        "server": ("test", 80),
        "client": ("test", 1),
    }
    sent = []

    async def quiet():
        if not sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()
        return None

    async def send(message):
        sent.append(message)
        if on_send is not None:
            on_send(message)

    await app(scope, receive or quiet, send)
    return sent


def body_of(sent):
    return b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")


def start_of(sent):
    return next(m for m in sent if m["type"] == "http.response.start")


def headers_of(sent):
    return {k.decode(): v.decode() for k, v in start_of(sent)["headers"]}


# --- GET of an open blob ---------------------------------------------------------------


async def test_get_streams_an_open_blob_until_sealed(store):
    bid = (await store.aput(DATA[:1000], seal=False)).id
    app = app_of(store, step=500)
    seen = []
    got = asyncio.Event()

    def on_send(message):
        if message["type"] == "http.response.body" and message.get("body"):
            seen.append(message["body"])
            got.set()

    request = asyncio.create_task(drive(app, "GET", url(bid), on_send=on_send))
    # Each piece arrives before the next is even written: the body follows.
    for offset in range(1000, len(DATA), 3000):
        await asyncio.wait_for(got.wait(), 10)
        got.clear()
        await store.aappend(bid, DATA[offset : offset + 3000])
    await asyncio.wait_for(got.wait(), 10)
    assert not request.done()
    await store.aseal(bid)
    sent = await asyncio.wait_for(request, 10)
    assert start_of(sent)["status"] == 200
    assert b"".join(seen) == DATA
    headers = headers_of(sent)
    assert headers["cache-control"] == OPEN_CACHE_CONTROL == "no-store"
    assert headers["x-blob-sealed"] == "0"
    assert "etag" not in headers
    assert "content-length" not in headers


def test_get_of_an_open_blob_through_a_client(client, store):
    bid = store.put(DATA[:4000], seal=False, mime="video/mp4", name="cam.mp4").id

    def finish():
        store.append(bid, DATA[4000:])
        store.seal(bid)

    writer = later(0.2, finish)
    try:
        response = client.get(url(bid))
    finally:
        writer.join(10)
    assert response.status_code == 200
    assert response.content == DATA
    assert response.headers["content-type"] == "video/mp4"
    assert response.headers["content-disposition"] == 'inline; filename="cam.mp4"'
    assert "content-length" not in response.headers


def test_get_once_sealed_is_immutable_again(client, store):
    bid = store.put(DATA, seal=False).id
    store.seal(bid)
    response = client.get(url(bid))
    assert response.headers["x-blob-sealed"] == "1"
    assert response.headers["etag"] == f'"{bid}"'
    assert "immutable" in response.headers["cache-control"]
    assert response.headers["content-length"] == str(len(DATA))


def test_head_of_an_open_blob(client, store):
    bid = store.put(DATA[:100], seal=False).id
    response = client.head(url(bid))
    assert response.status_code == 200
    assert response.headers["x-blob-sealed"] == "0"
    assert response.headers["cache-control"] == "no-store"
    assert "etag" not in response.headers
    assert "content-length" not in response.headers


def test_range_inside_an_open_blob(client, store):
    bid = store.put(DATA[:5000], seal=False).id
    response = client.get(url(bid), headers={"range": "bytes=100-199"})
    assert response.status_code == 206
    assert response.content == DATA[100:200]
    assert response.headers["content-range"] == "bytes 100-199/*"
    assert response.headers["x-blob-sealed"] == "0"


def test_range_past_the_size_waits_for_the_bytes(client, store):
    bid = store.put(DATA[:1000], seal=False).id
    writer = later(0.2, store.append, bid, DATA[1000:5000])
    try:
        response = client.get(url(bid), headers={"range": "bytes=500-2999"})
    finally:
        writer.join(10)
    assert response.status_code == 206
    assert response.content == DATA[500:3000]
    assert response.headers["content-range"] == "bytes 500-2999/*"


def test_open_ended_range_serves_what_is_there(client, store):
    bid = store.put(DATA[:1000], seal=False).id
    response = client.get(url(bid), headers={"range": "bytes=400-"})
    assert response.status_code == 206
    assert response.content == DATA[400:1000]
    assert response.headers["content-range"] == "bytes 400-999/*"


def test_open_ended_range_past_the_end_is_416(client, store):
    bid = store.put(DATA[:1000], seal=False).id
    response = client.get(url(bid), headers={"range": "bytes=1000-"})
    assert response.status_code == 416
    assert response.headers["content-range"] == "bytes */*"


@pytest.mark.parametrize(
    "headers",
    [
        {"range": "bytes=0-"},
        {"range": "bytes=-100"},
        {"range": "bytes=10-20", "if-range": '"anything"'},
    ],
    ids=["from-zero", "suffix", "if-range"],
)
def test_ranges_that_serve_the_whole_open_blob(client, store, headers):
    bid = store.put(DATA[:1000], seal=False).id
    writer = later(0.2, store.seal, bid)
    try:
        response = client.get(url(bid), headers=headers)
    finally:
        writer.join(10)
    assert response.status_code == 200
    assert response.content == DATA[:1000]


async def test_idle_breaks_the_body_off(store):
    bid = (await store.aput(b"abc", seal=False)).id
    app = app_of(store, idle=0.1)
    with pytest.raises(BlobIdle):
        await drive(app, "GET", url(bid))


# --- POST is readable while it uploads -----------------------------------------------


async def test_upload_is_readable_while_it_runs(store):
    app = app_of(store)
    go = asyncio.Event()
    chunks = [DATA[:6000], DATA[6000:]]

    async def receive():
        if chunks:
            if len(chunks) == 1:
                await go.wait()  # the second chunk waits for the reader
            return {"type": "http.request", "body": chunks.pop(0), "more_body": bool(chunks)}
        await asyncio.Event().wait()
        return None

    upload = asyncio.create_task(
        drive(app, "POST", AT, headers=[("content-type", "x/y")], receive=receive)
    )
    for _ in range(200):
        ids = await asyncio.to_thread(stored_ids, store)
        if ids:
            break
        await asyncio.sleep(0.02)
    (bid,) = ids
    info = await store.ainfo(bid)
    assert not info.sealed
    assert 0 < info.size <= 6000
    reading = asyncio.create_task(drive(app, "GET", url(bid)))
    await asyncio.sleep(0.1)
    go.set()
    posted = await asyncio.wait_for(upload, 10)
    assert start_of(posted)["status"] == 201
    read = await asyncio.wait_for(reading, 10)
    assert body_of(read) == DATA
    assert (await store.ainfo(bid)).sealed
