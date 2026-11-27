"""A blob store over HTTP: GET with ranges and caching, HEAD, streamed upload, one store per mount.

Every test runs on each backend (``backend`` in ``_support.blob_fixtures``):
lmdb and files on ``tmp_path``, s3 on moto. The memory test runs the local
ones only, since moto holds every byte it is sent.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import tracemalloc
from urllib.parse import quote

import boto3
import httpx
import pytest
from _support import blob_fixtures
from _support.blob_workers import BUCKET
from _support.brackets import config
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount
from starlette.testclient import TestClient

import nu
import nustd.blob
from nustd.blob import FilesBackend, LMDBBackend
from nustd.blob.http import BlobMount
from nustd.blob.http.serving import (
    CACHE_CONTROL,
    MAX_FIELD,
    HeldOpen,
    routes,
    same_origin,
    serve_blobs,
)


SIZE = 3000
DATA = bytes(range(251)) * (SIZE // 251) + bytes(range(SIZE % 251))
MISSING = "0" * 32
AT = "/media"
MEDIA = BlobMount(AT)

# The per-backend fixtures, shared with tests/nustd/blob.
moto_s3 = blob_fixtures.moto_s3
kind = blob_fixtures.kind
store_path = blob_fixtures.store_path
backend = blob_fixtures.backend


class Spy:
    """A backend that records which calls reach it, and can run a hook after ``ainfo``."""

    def __init__(self, backend):
        self.backend = backend
        self.calls = []
        self.after_info = None
        self.pieces_in = []

    def __getattr__(self, name):
        attr = getattr(self.backend, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append(name)
            return attr(*args, **kwargs)

        return call

    async def ainfo(self, blob_id):
        self.calls.append("ainfo")
        info = await self.backend.ainfo(blob_id)
        if self.after_info is not None:
            self.after_info(blob_id)
        return info

    @property
    def reads(self):
        return [c for c in self.calls if c in ("read", "stream", "aread", "astream")]


@pytest.fixture
def spy(backend):
    return Spy(backend)


def make_client(backend, mount=MEDIA, raise_server_exceptions=True, **kwargs):
    return TestClient(
        Starlette(routes=routes(mount, backend, **kwargs)),
        raise_server_exceptions=raise_server_exceptions,
    )


@pytest.fixture
def client(spy):
    with make_client(spy) as client:
        yield client


@pytest.fixture
def blob(backend):
    return backend.put(DATA, mime="application/x-test", name="data.bin")


def url(blob_id):
    return f"{AT}/{blob_id}"


def stored(backend, kind):
    """How many blobs the backend holds, read from its own storage."""
    if kind == "files":
        return len(list((backend.root / "blobs").rglob("*.json")))
    if kind == "lmdb":
        with backend._env.begin() as txn:
            return txn.stat(backend._meta)["entries"]
    listed = boto3.client("s3").list_objects_v2(Bucket=BUCKET, Prefix=backend.prefix)
    return listed.get("KeyCount", 0)


# --- GET ---------------------------------------------------------------------


def test_get_whole(client, blob):
    response = client.get(url(blob.id))
    assert response.status_code == 200
    assert response.content == DATA
    headers = response.headers
    assert headers["etag"] == f'"{blob.id}"'
    assert headers["cache-control"] == CACHE_CONTROL == "public, max-age=31536000, immutable"
    assert headers["content-type"] == "application/x-test"
    assert headers["accept-ranges"] == "bytes"
    assert headers["content-length"] == str(SIZE)
    assert headers["content-disposition"] == 'inline; filename="data.bin"'
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-blob-sealed"] == "1"
    assert "content-range" not in headers


async def _asgi(app, method, path, headers=(), messages=None):
    """Every message the app sends for one request, driven over raw ASGI.

    ``messages`` are what ``receive`` gives, in order; an empty body by default.
    """
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
    pending = list(messages or [{"type": "http.request", "body": b"", "more_body": False}])
    sent = []

    async def receive():
        if pending:
            return pending.pop(0)
        await asyncio.Event().wait()  # nothing more ever arrives
        return None

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    return sent


def _status(sent):
    return next(m["status"] for m in sent if m["type"] == "http.response.start")


async def _asgi_get(app, path):
    """The body messages a GET sends, as the server sends them."""
    sent = await _asgi(app, "GET", path)
    return [m["body"] for m in sent if m["type"] == "http.response.body" and m["body"]]


def test_get_streams_in_steps(spy, blob):
    app = Starlette(routes=routes(MEDIA, spy, step=1000))
    pieces = asyncio.run(_asgi_get(app, url(blob.id)))
    assert pieces == [DATA[:1000], DATA[1000:2000], DATA[2000:]]


def test_get_empty_blob(client, backend):
    info = backend.put(b"")
    response = client.get(url(info.id), headers={"range": "bytes=0-"})
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["content-length"] == "0"


def test_no_mime_no_name(client, backend):
    info = backend.put(b"abc")
    headers = client.get(url(info.id)).headers
    assert headers["content-type"] == "application/octet-stream"
    assert "content-disposition" not in headers


def test_unsafe_mime_falls_back(client, backend):
    info = backend.put(b"abc", mime="text/plain\r\nx-evil: 1")
    response = client.get(url(info.id))
    assert response.headers["content-type"] == "application/octet-stream"
    assert "x-evil" not in response.headers


def test_non_ascii_name(client, backend):
    info = backend.put(b"abc", name='кот "1".png')
    disposition = client.get(url(info.id)).headers["content-disposition"]
    assert disposition == (
        "inline; filename=\"___ _1_.png\"; filename*=UTF-8''" + quote('кот "1".png', safe="")
    )


def test_download_asks_to_save(client, backend):
    info = backend.put(b"abc", name="report.pdf")
    response = client.get(url(info.id) + "?download=1")
    assert response.headers["content-disposition"] == 'attachment; filename="report.pdf"'
    assert response.content == b"abc"
    assert (
        client.get(url(info.id) + "?download=0").headers["content-disposition"].startswith("inline")
    )


def test_download_without_a_name_is_still_an_attachment(client, backend):
    info = backend.put(b"abc")
    assert client.get(url(info.id) + "?download=1").headers["content-disposition"] == "attachment"
    assert client.head(url(info.id) + "?download=1").headers["content-disposition"] == "attachment"


def test_name_control_chars_dropped(client, backend):
    info = backend.put(b"abc", name="a\r\nb.txt")
    assert client.get(url(info.id)).headers["content-disposition"] == 'inline; filename="ab.txt"'


@pytest.mark.parametrize(
    ("spec", "start", "end"),
    [
        ("bytes=0-99", 0, 100),
        ("bytes=100-199", 100, 200),
        ("bytes=2990-", 2990, SIZE),  # open range
        ("bytes=-500", SIZE - 500, SIZE),  # suffix
        ("bytes=-99999", 0, SIZE),  # suffix longer than the blob
        ("bytes=2900-99999", 2900, SIZE),  # end clamped
        ("bytes=0-" + "9" * 40, 0, SIZE),  # end too long to parse, clamped
        ("bytes=7-7", 7, 8),
        ("BYTES = 5-9", 5, 10),
    ],
)
def test_range(client, blob, spec, start, end):
    response = client.get(url(blob.id), headers={"range": spec})
    assert response.status_code == 206
    assert response.content == DATA[start:end]
    assert response.headers["content-range"] == f"bytes {start}-{end - 1}/{SIZE}"
    assert response.headers["content-length"] == str(end - start)
    assert response.headers["etag"] == f'"{blob.id}"'
    assert response.headers["cache-control"] == CACHE_CONTROL


@pytest.mark.parametrize(
    "spec", ["bytes=3000-", "bytes=5000-6000", "bytes=-0", "bytes=1" + "0" * 40 + "-"]
)
def test_range_not_satisfiable(client, blob, spec):
    response = client.get(url(blob.id), headers={"range": spec})
    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{SIZE}"
    assert response.content == b""


@pytest.mark.parametrize(
    "spec",
    [
        "bytes=0-1,5-6",  # several ranges: served whole
        "bytes=0-1, 4000-5000",
        "bytes=9-3",  # last before first
        "bytes=-",
        "bytes=abc",
        "bytes=\u00b2-".encode("latin-1"),  # a unicode digit is no digit
        "items=0-9",
        "0-9",
    ],
)
def test_range_ignored_serves_whole(client, blob, spec):
    response = client.get(url(blob.id), headers={"range": spec})
    assert response.status_code == 200
    assert response.content == DATA
    assert "content-range" not in response.headers


def test_if_range(client, blob):
    etag = f'"{blob.id}"'
    held = client.get(url(blob.id), headers={"range": "bytes=0-9", "if-range": etag})
    assert held.status_code == 206
    assert held.content == DATA[:10]
    for other in (f'"{MISSING}"', f"W/{etag}", "Wed, 21 Oct 2015 07:28:00 GMT"):
        stale = client.get(url(blob.id), headers={"range": "bytes=0-9", "if-range": other})
        assert stale.status_code == 200
        assert stale.content == DATA


@pytest.mark.parametrize(
    "tag",
    ['"{id}"', 'W/"{id}"', '"{other}", "{id}"', "*"],
)
def test_not_modified(client, blob, spy, tag):
    header = tag.format(id=blob.id, other=MISSING)
    for method in ("GET", "HEAD"):
        response = client.request(method, url(blob.id), headers={"if-none-match": header})
        assert response.status_code == 304
        assert response.content == b""
        assert response.headers["etag"] == f'"{blob.id}"'
        assert response.headers["cache-control"] == CACHE_CONTROL
    assert spy.reads == []


def test_not_modified_wins_over_range(client, blob, spy):
    response = client.get(
        url(blob.id), headers={"if-none-match": f'"{blob.id}"', "range": "bytes=0-9"}
    )
    assert response.status_code == 304
    assert response.content == b""
    assert spy.reads == []


def test_none_match_other_tag(client, blob):
    response = client.get(url(blob.id), headers={"if-none-match": f'"{MISSING}"'})
    assert response.status_code == 200
    assert response.content == DATA


@pytest.mark.parametrize(
    "path",
    [
        f"/media/{MISSING}",  # unknown id
        f"/other/{'a' * 32}",  # outside the mount
        "/media/nope",  # malformed ids
        f"/media/{'A' * 32}",
        f"/media/{'a' * 33}",
        "/media/..%2F..%2Fetc",
    ],
)
def test_not_found(client, path):
    for method in ("GET", "HEAD"):
        response = client.request(method, path)
        assert response.status_code == 404


def test_deleted_after_info_is_404(client, blob, spy):
    spy.after_info = spy.backend.delete
    response = client.get(url(blob.id))
    assert response.status_code == 404


# --- HEAD --------------------------------------------------------------------


def test_head(client, blob, spy):
    response = client.head(url(blob.id), headers={"range": "bytes=0-9"})
    assert response.status_code == 200  # HEAD ignores Range
    assert response.content == b""
    assert response.headers["content-length"] == str(SIZE)
    assert response.headers["etag"] == f'"{blob.id}"'
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-type"] == "application/x-test"
    assert response.headers["cache-control"] == CACHE_CONTROL
    assert response.headers["x-blob-sealed"] == "1"
    assert "content-range" not in response.headers
    assert spy.calls == ["ainfo"]
    assert spy.reads == []


# --- POST --------------------------------------------------------------------


def test_upload_then_ranged_get(client, backend):
    name = "Ծաղիկ 1.png"
    response = client.post(
        "/media",
        content=DATA,
        headers={"content-type": "image/png", "x-blob-name": quote(name)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "size": SIZE, "mime": "image/png", "name": name}
    assert response.headers["location"] == url(body["id"])
    assert backend.read(body["id"]) == DATA

    ranged = client.get(response.headers["location"], headers={"range": "bytes=-500"})
    assert ranged.status_code == 206
    assert ranged.content == DATA[-500:]
    assert ranged.headers["content-type"] == "image/png"
    assert "filename*=UTF-8''" in ranged.headers["content-disposition"]


def test_upload_name_from_query_and_charset_kept(client, backend):
    response = client.post(
        "/media?name=notes%20one.txt",
        content=b"hi",
        headers={"content-type": "text/plain; charset=utf-8"},
    )
    assert response.status_code == 201
    info = backend.info(response.json()["id"])
    assert info.name == "notes one.txt"
    assert info.mime == "text/plain; charset=utf-8"
    assert client.get(url(info.id)).headers["content-type"] == "text/plain; charset=utf-8"


def test_upload_empty(client, backend):
    response = client.post("/media", content=b"")
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert response.json()["mime"] == ""


def test_upload_header_name_wins_over_query(client, backend):
    response = client.post(
        "/media?name=query.txt", content=b"hi", headers={"x-blob-name": "header.txt"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "header.txt"
    assert backend.info(response.json()["id"]).name == "header.txt"


@pytest.mark.parametrize(
    ("path", "headers"),
    [
        ("/media?name=" + "a" * 3000, {}),
        ("/media", {"x-blob-name": "a" * (MAX_FIELD + 1)}),
        ("/media", {"content-type": "text/plain; x=" + "b" * 3000}),
    ],
    ids=["query-name", "header-name", "mime"],
)
def test_upload_oversized_field_is_400(spy, kind, path, headers):
    with make_client(spy) as client:
        response = client.post(path, content=b"abc", headers=headers)
    assert response.status_code == 400
    assert "aput" not in spy.calls
    assert stored(spy.backend, kind) == 0


def test_upload_field_at_bound_is_stored_or_400(backend, kind):
    """A name within the bound that s3's metadata still cannot hold is a 400 there, not a 500."""
    name = "ф" * MAX_FIELD  # 6 bytes each once percent-encoded for s3
    with make_client(backend) as client:
        response = client.post("/media", content=b"abc", headers={"x-blob-name": quote(name)})
    if kind == "s3":
        assert response.status_code == 400
        assert "metadata" in response.text
        assert stored(backend, kind) == 0
    else:
        assert response.status_code == 201
        assert backend.info(response.json()["id"]).name == name


def test_upload_value_error_after_reading_is_not_400(backend):
    """Only a refusal before the body is read is the client's; a later ValueError stays a 500."""

    async def aput(source, **kwargs):
        async for _ in source:
            raise ValueError("backend broke mid-put")
        return None

    backend.aput = aput
    with make_client(backend, raise_server_exceptions=False) as client:
        response = client.post("/media", content=b"abc")
    assert response.status_code == 500


def test_upload_outside_the_mount_is_404(client):
    assert client.post("/other", content=b"x").status_code == 404


def test_upload_over_declared_cap_reads_nothing(spy, kind):
    with make_client(spy, BlobMount(AT, max_upload=100)) as client:
        response = client.post("/media", content=b"x" * 101)
    assert response.status_code == 413
    assert "aput" not in spy.calls
    assert stored(spy.backend, kind) == 0


def multipart_uploads(backend):
    """The s3 multipart uploads still open under the backend's prefix."""
    listed = boto3.client("s3").list_multipart_uploads(Bucket=BUCKET, Prefix=backend.prefix)
    return listed.get("Uploads", [])


def test_upload_declared_huge_reads_nothing(spy, kind):
    """A Content-Length too long to parse as a machine int is still over the cap."""
    app = Starlette(routes=routes(BlobMount(AT, max_upload=100), spy))
    sent = asyncio.run(_asgi(app, "POST", "/media", [("content-length", "9" * 40)]))
    assert _status(sent) == 413
    assert "aput" not in spy.calls
    assert stored(spy.backend, kind) == 0


def test_upload_client_disconnect_stores_nothing(backend, kind):
    app = Starlette(routes=routes(MEDIA, backend))
    messages = [
        {"type": "http.request", "body": b"x" * 1000, "more_body": True},
        {"type": "http.disconnect"},
    ]
    asyncio.run(_asgi(app, "POST", "/media", messages=messages))
    assert stored(backend, kind) == 0
    assert blob_fixtures.leftovers(backend) == []


def test_upload_over_cap_streamed_stores_nothing(spy, kind):
    def body():
        for _ in range(10):
            yield b"x" * 64

    with make_client(spy, BlobMount(AT, max_upload=500)) as client:
        response = client.post("/media", content=body())  # chunked: no Content-Length
        assert response.status_code == 413
        assert stored(spy.backend, kind) == 0
        ok = client.post("/media", content=b"x" * 500)
        assert ok.status_code == 201
    assert stored(spy.backend, kind) == 1
    assert blob_fixtures.leftovers(spy.backend) == []


@pytest.mark.parametrize("kind", ["s3"])
def test_s3_cap_past_one_part_aborts_the_upload(moto_s3, backend, kind):
    """A capped upload that already sent a part leaves no open multipart upload behind."""
    part = backend.part_size

    def body():
        for _ in range(3):
            yield b"x" * part

    with make_client(backend, BlobMount(AT, max_upload=2 * part)) as client:
        response = client.post("/media", content=body())
    assert response.status_code == 413
    assert stored(backend, kind) == 0
    assert multipart_uploads(backend) == []


@pytest.mark.parametrize("kind", ["lmdb", "files"])
def test_backend_cap_is_413(backend):
    backend.max_size = 100
    with make_client(backend) as client:
        response = client.post("/media", content=iter([b"x" * 80, b"x" * 80]))
    assert response.status_code == 413
    assert blob_fixtures.leftovers(backend) == []


async def _post_stream(backend, total, piece, on_piece=None):
    """POST ``total`` bytes in ``piece`` sized parts through ASGI, which streams the body."""
    sent = 0

    async def body():
        nonlocal sent
        for offset in range(0, total, piece):
            sent += 1
            if on_piece is not None:
                on_piece(sent)
            yield b"\xab" * min(piece, total - offset)
            await asyncio.sleep(0)

    app = Starlette(routes=routes(MEDIA, backend))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/media", content=body())


def test_upload_reaches_backend_while_body_still_arrives(backend):
    """The backend takes each piece as it arrives, not after the whole body is read."""
    sent_when_seen = []
    sent = [0]
    real_aput = backend.aput

    async def aput(source, **kwargs):
        async def watched():
            async for piece in source:
                sent_when_seen.append(sent[0])
                yield piece

        return await real_aput(watched(), **kwargs)

    backend.aput = aput
    pieces = 40

    def on_piece(count):
        sent[0] = count

    response = asyncio.run(_post_stream(backend, pieces * 65536, 65536, on_piece))
    assert response.status_code == 201
    assert response.json()["size"] == pieces * 65536
    assert len(sent_when_seen) == pieces
    # Piece k reaches the backend before the client has sent piece k + 2.
    assert all(seen <= index + 2 for index, seen in enumerate(sent_when_seen, start=1))


@pytest.mark.parametrize("kind", ["lmdb", "files"])
def test_large_upload_is_not_buffered(backend):
    total = 64 << 20
    if isinstance(backend, LMDBBackend):
        backend.batch_size = 8 << 20  # what an LMDB put holds: an eighth of the upload
    tracemalloc.start()
    try:
        response = asyncio.run(_post_stream(backend, total, 256 << 10))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert response.status_code == 201
    info = backend.info(response.json()["id"])
    assert info.size == total
    assert peak < 16 << 20, f"peak {peak} bytes for a {total} byte upload"


# --- cross-site uploads ------------------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        {"sec-fetch-site": "cross-site"},
        {"sec-fetch-site": "same-site"},
        {"origin": "http://evil.test"},
    ],
    ids=["cross-site", "same-site", "foreign-origin"],
)
def test_cross_site_upload_is_403(spy, kind, headers):
    with make_client(spy) as client:
        response = client.post(AT, content=b"abc", headers=headers)
    assert response.status_code == 403
    assert "aput" not in spy.calls
    assert stored(spy.backend, kind) == 0


def test_cross_site_mount_takes_the_upload(backend):
    with make_client(backend, BlobMount(AT, cross_site=True)) as client:
        response = client.post(AT, content=b"abc", headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 201
    assert backend.read(response.json()["id"]) == b"abc"


def test_own_page_upload_passes(backend):
    with make_client(backend) as client:
        own = client.post(AT, content=b"a", headers={"sec-fetch-site": "same-origin"})
        same_host = client.post(AT, content=b"b", headers={"origin": "http://testserver"})
    assert own.status_code == 201
    assert same_host.status_code == 201


def test_cross_site_read_is_served(client, blob):
    """Only uploads are guarded: a page anywhere may show a blob."""
    response = client.get(url(blob.id), headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 200
    assert response.content == DATA


def _request(headers):
    scope = {
        "type": "http",
        "method": "POST",
        "path": AT,
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({}, True),  # no browser: curl, a script
        ({"sec-fetch-site": "same-origin"}, True),
        ({"sec-fetch-site": "none"}, True),  # typed by the user
        ({"sec-fetch-site": "same-site"}, False),
        ({"sec-fetch-site": "cross-site"}, False),
        # Sec-Fetch-Site decides when sent: it holds behind a dev proxy.
        ({"sec-fetch-site": "same-origin", "origin": "http://evil.test", "host": "a.test"}, True),
        ({"sec-fetch-site": "cross-site", "origin": "http://a.test", "host": "a.test"}, False),
        ({"origin": "http://a.test", "host": "a.test"}, True),
        ({"origin": "https://a.test:8443", "host": "a.test:8443"}, True),
        ({"origin": "http://a.test:8080", "host": "a.test"}, False),
        ({"origin": "http://evil.test", "host": "a.test"}, False),
        ({"origin": "null", "host": "a.test"}, False),
        ({"origin": "http://a.test"}, False),  # no Host to match
    ],
)
def test_same_origin(headers, expected):
    assert same_origin(_request(headers)) is expected


# --- mounting and boundaries -------------------------------------------------


def test_two_mounts_stay_apart(tmp_path):
    a = FilesBackend(tmp_path / "a")
    b = FilesBackend(tmp_path / "b")
    a.open()
    b.open()
    blob = a.put(b"in a")
    served = routes(BlobMount("/files/a"), a) + routes(BlobMount("/files/b"), b)
    with TestClient(Starlette(routes=served)) as client:
        assert client.get(f"/files/a/{blob.id}").content == b"in a"
        assert client.get(f"/files/b/{blob.id}").status_code == 404
        assert client.get(f"/media/{blob.id}").status_code == 404
        posted = client.post("/files/b", content=b"in b")
        assert posted.headers["location"] == f"/files/b/{posted.json()['id']}"
        assert b.read(posted.json()["id"]) == b"in b"


def test_routes_are_one_get_and_one_post():
    served = routes(BlobMount("/files/media"), object())
    assert [(r.path, sorted(r.methods)) for r in served] == [
        ("/files/media/{blob_id}", ["GET", "HEAD"]),
        ("/files/media", ["POST"]),
    ]


def test_location_under_mount(backend):
    app = Starlette(routes=[Mount("/api", routes=routes(MEDIA, backend))])
    with TestClient(app) as client:
        posted = client.post(f"/api{AT}", content=DATA)
        assert posted.status_code == 201
        location = posted.headers["location"]
        assert location == f"/api{AT}/{posted.json()['id']}"
        assert client.get(location).content == DATA


def test_mounts_on_web_server(backend, blob):
    from nustd.ws_server import WebServer

    class _Session:
        def __init__(self, ws):
            self.ws = ws

        async def run_intake(self):
            return None

    app = WebServer(session_cls=_Session, routes=routes(MEDIA, backend))._build_app()
    with TestClient(app) as client:
        assert client.get(url(blob.id), headers={"range": "bytes=0-4"}).content == DATA[:5]


def test_step_must_be_positive(tmp_path):
    with pytest.raises(ValueError, match="step"):
        routes(MEDIA, FilesBackend(tmp_path), step=0)


# --- serve_blobs ---------------------------------------------------------------


def _held(bracket):
    """The backend a ``HeldOpen`` bracket opens."""
    assert config(bracket)["cls"] is HeldOpen
    return config(bracket)["kwargs"]["backend"]


def test_serve_blobs_brackets_and_routes_each_mount(tmp_path):
    files = BlobMount("/files")
    pics = BlobMount("/pics", max_upload=10)
    given = [FilesBackend(tmp_path / "files"), LMDBBackend(tmp_path / "pics")]
    brackets, served = serve_blobs({files: given[0], pics: given[1]})
    assert len(brackets) == 2
    assert [r.path for r in served] == ["/files/{blob_id}", "/files", "/pics/{blob_id}", "/pics"]
    held = [_held(bracket) for bracket in brackets]
    assert all(h is g for h, g in zip(held, given, strict=True))
    assert not (tmp_path / "files").exists()  # not opened by serve_blobs
    for b in held:
        b.open()
    try:
        # The routes serve the very backends the brackets hold open.
        with TestClient(Starlette(routes=served)) as client:
            posted = client.post("/files", content=b"in files")
            assert posted.status_code == 201
            assert client.get(posted.headers["location"]).content == b"in files"
            assert client.post("/pics", content=b"x" * 11).status_code == 413
            assert client.post("/pics", content=b"x" * 10).status_code == 201
    finally:
        for b in held:
            b.close()


class _Opens(FilesBackend):
    events: list[str] = []  # noqa: RUF012

    def open(self):
        _Opens.events.append("open")
        super().open()

    def close(self):
        _Opens.events.append("close")
        super().close()


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_held_open_spans_the_tree(tmp_path, mode):
    """Each mount's bracket opens its backend before the body and closes it after."""
    _Opens.events.clear()
    brackets, _ = serve_blobs(
        {
            BlobMount("/files"): _Opens(tmp_path / "files"),
            BlobMount("/pics"): _Opens(tmp_path / "pics"),
        }
    )
    term = nu.With(*brackets, body=nu.Literal(1))
    out = nu.run(term)[0] if mode == "sync" else asyncio.run(nu.arun(term))[0]
    assert out == 1
    assert _Opens.events == ["open", "open", "close", "close"]


def test_one_backend_under_two_mounts_is_held_open_once(tmp_path):
    """Two mounts may serve one store, each with its own rules; it opens and closes once."""
    _Opens.events.clear()
    shared = _Opens(tmp_path / "files")
    brackets, served = serve_blobs(
        {BlobMount("/files"): shared, BlobMount("/small", max_upload=1): shared}
    )
    assert len(brackets) == 1
    assert _held(brackets[0]) is shared
    assert [r.path for r in served] == ["/files/{blob_id}", "/files", "/small/{blob_id}", "/small"]
    nu.run(nu.With(*brackets, body=nu.Literal(1)))
    assert _Opens.events == ["open", "close"]


def test_held_open_opens_and_closes_its_backend(tmp_path):
    env = LMDBBackend(tmp_path / "env")
    held = HeldOpen(env)
    held.setup(None)
    info = env.put(b"x")
    held.cleanup()
    with pytest.raises(RuntimeError, match="not open"):
        env.read(info.id)
    asyncio.run(held.asetup(None))
    assert env.read(info.id) == b"x"
    asyncio.run(held.acleanup())
    with pytest.raises(RuntimeError, match="not open"):
        env.read(info.id)


def test_serve_blobs_refuses_a_key_that_is_no_mount(tmp_path):
    with pytest.raises(TypeError, match="BlobMount"):
        serve_blobs({"/files": FilesBackend(tmp_path)})


def test_serve_blobs_refuses_two_stores_at_one_path(tmp_path):
    blobs = {
        BlobMount("/files"): FilesBackend(tmp_path / "a"),
        BlobMount("/files"): FilesBackend(tmp_path / "b"),
    }
    with pytest.raises(ValueError, match="two stores mounted at '/files'"):
        serve_blobs(blobs)


def test_serve_blobs_refuses_a_spec(tmp_path):
    """The server takes a backend; the spec is the tree's."""
    with pytest.raises(TypeError, match="takes a backend"):
        serve_blobs({BlobMount("/files"): nustd.blob.files("files", tmp_path)})


@pytest.mark.parametrize("bad", [None, "/var/blobs", FilesBackend], ids=["none", "str", "class"])
def test_serve_blobs_refuses_what_is_no_backend(bad):
    with pytest.raises(TypeError, match="needs a blob backend"):
        serve_blobs({BlobMount("/files"): bad})


def test_serve_blobs_is_exported():
    assert nustd.blob.http.serve_blobs is serve_blobs
    assert "serve_blobs" in nustd.blob.http.__all__
    for gone in ("routes", "Store", "URL_PREFIX"):
        assert not hasattr(nustd.blob, gone)
        assert gone not in nustd.blob.__all__


def _modules_after(statement):
    code = f"import sys\n{statement}\nprint('\\n'.join(sorted(sys.modules)))"
    out = subprocess.run(  # noqa: S603 - our own interpreter on a fixed statement
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    return set(out.split())


def test_import_blob_needs_no_starlette():
    loaded = _modules_after("import nustd.blob")
    assert "starlette" not in loaded
    assert "nustd.blob.http.serving" not in loaded


def test_import_mount_needs_no_starlette():
    """``BlobMount`` is plain; the routes load with ``serve_blobs``, on first use."""
    loaded = _modules_after("import nustd.blob; nustd.blob.http.BlobMount('/files')")
    assert "starlette" not in loaded
    assert "nustd.blob.http.serving" not in loaded
