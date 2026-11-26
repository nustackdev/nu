"""The upload intake: the temp area on disk and the route that fills it.

A real ``UploadArea`` in a tmp dir, set up against a real ``WebServer`` that
is never started: its connection book is poked directly, which is what the
route reads for a live tab and what the area follows to sweep a closed one.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
import uuid
from typing import TYPE_CHECKING

import pytest
from _support.brackets import config
from starlette.applications import Starlette
from starlette.testclient import TestClient

import nu
from nu.context import FabricRef
from nu.lang.runtime import Context
from nustd.session import SessionId
from nustd.ui.nudle import serve
from nustd.ui.uploads import (
    STALE_AFTER,
    UPLOAD_PREFIX,
    UploadArea,
    UploadView,
    upload_view,
    uploads,
)
from nustd.ui.uploads.intake import same_origin
from nustd.ws_server import WebServer
from nustd.ws_server.fabric import _Connection


if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


SAME = {"Sec-Fetch-Site": "same-origin"}


class _Session:
    async def run_intake(self) -> None:
        return None


class _Rig:
    """An area set up against a server whose book the test drives."""

    def __init__(self, root: Path, cap: int | None = 1 << 20) -> None:
        self.server = WebServer(session_cls=_Session)
        bracket, routes = uploads(root, cap=cap)
        self.area: UploadArea = bracket.area
        self.ctx = Context().bind(WebServer, self.server)
        self.area.setup(self.ctx)
        self.app = Starlette(routes=routes)

    def open_tab(self) -> str:
        sid = uuid.uuid4().hex
        self.server._connections[sid] = _Connection(_Session())
        self.server._channel.emit(sid)
        return sid

    def close_tab(self, sid: str) -> None:
        self.server._connections.pop(sid, None)
        self.server._channel.emit(sid)

    def files(self, sid: str) -> list[str]:
        home = self.area.root / sid
        return sorted(p.name for p in home.iterdir()) if home.exists() else []


@pytest.fixture
def rig(tmp_path: Path) -> Iterator[_Rig]:
    r = _Rig(tmp_path / "area")
    yield r
    r.area.cleanup()


@pytest.fixture
def client(rig: _Rig) -> Iterator[TestClient]:
    with TestClient(rig.app) as c:
        yield c


def _url(sid: str) -> str:
    return f"{UPLOAD_PREFIX}/{sid}"


# ---- the route ---------------------------------------------------------------


def test_a_post_lands_the_file_and_answers_token_and_size(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    res = client.post(_url(sid), content=b"a,b\n1,2\n", headers=SAME)
    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"token", "size"}
    assert body["size"] == 8
    assert rig.files(sid) == [body["token"]]
    assert rig.area.path(sid, body["token"]).read_bytes() == b"a,b\n1,2\n"


def test_an_empty_body_lands_an_empty_file(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    res = client.post(_url(sid), content=b"", headers=SAME)
    assert res.status_code == 201
    assert rig.area.path(sid, res.json()["token"]).read_bytes() == b""


def test_a_matching_origin_passes_without_fetch_metadata(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    res = client.post(_url(sid), content=b"x", headers={"Origin": "http://testserver"})
    assert res.status_code == 201


@pytest.mark.parametrize(
    "headers",
    [
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
        {"Sec-Fetch-Site": "none"},
        {"Sec-Fetch-Site": "cross-site", "Origin": "http://testserver"},
        {"Origin": "http://evil.example"},
        {"Origin": "http://testserver:9999"},
        {"Origin": "null"},
        {},
    ],
)
def test_cross_site_is_refused_and_lands_nothing(rig: _Rig, client: TestClient, headers: dict):
    sid = rig.open_tab()
    res = client.post(_url(sid), content=b"x", headers=headers)
    assert res.status_code == 403
    assert rig.files(sid) == []


def test_an_unknown_sid_is_refused(rig: _Rig, client: TestClient):
    res = client.post(_url(uuid.uuid4().hex), content=b"x", headers=SAME)
    assert res.status_code == 403
    assert list(rig.area.root.iterdir()) == []


def test_a_closed_tab_is_refused(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    rig.close_tab(sid)
    assert client.post(_url(sid), content=b"x", headers=SAME).status_code == 403


def test_a_malformed_sid_is_refused(rig: _Rig, client: TestClient):
    assert client.post(f"{UPLOAD_PREFIX}/..", content=b"x", headers=SAME).status_code in (403, 404)


def test_over_cap_by_content_length_is_refused_before_reading(tmp_path: Path):
    rig = _Rig(tmp_path / "area", cap=4)
    try:
        sid = rig.open_tab()
        with TestClient(rig.app) as client:
            res = client.post(_url(sid), content=b"12345", headers=SAME)
        assert res.status_code == 413
        assert "4 bytes" in res.text
        assert rig.files(sid) == []
    finally:
        rig.area.cleanup()


def test_exactly_the_cap_lands(tmp_path: Path):
    rig = _Rig(tmp_path / "area", cap=4)
    try:
        sid = rig.open_tab()
        with TestClient(rig.app) as client:
            assert client.post(_url(sid), content=b"1234", headers=SAME).status_code == 201
    finally:
        rig.area.cleanup()


def test_over_cap_mid_stream_is_cut_and_leaves_nothing(tmp_path: Path):
    rig = _Rig(tmp_path / "area", cap=10)
    try:
        sid = rig.open_tab()

        def chunks() -> Iterator[bytes]:
            for _ in range(5):
                yield b"abcd"

        with TestClient(rig.app) as client:
            res = client.post(_url(sid), content=chunks(), headers=SAME)
        assert res.status_code == 413
        assert rig.files(sid) == []
    finally:
        rig.area.cleanup()


def test_a_chunked_body_under_cap_lands_whole(rig: _Rig, client: TestClient):
    sid = rig.open_tab()

    def chunks() -> Iterator[bytes]:
        for i in range(4):
            yield bytes([65 + i]) * 1000

    res = client.post(_url(sid), content=chunks(), headers=SAME)
    assert res.status_code == 201
    assert res.json()["size"] == 4000
    assert rig.area.path(sid, res.json()["token"]).read_bytes()[::1000] == b"ABCD"


# ---- pieces ------------------------------------------------------------------


def _piece(client: TestClient, sid: str, body: bytes, total: int, token: str = "", at: int = 0):
    query = f"token={token}&offset={at}&total={total}" if token else f"total={total}"
    return client.post(f"{_url(sid)}?{query}", content=body, headers=SAME)


def test_pieces_land_the_file_once_the_last_is_in(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    first = _piece(client, sid, b"abcd", 10)
    assert first.status_code == 202
    token = first.json()["token"]
    assert first.json() == {"token": token, "size": 4}
    assert rig.files(sid) == [f"{token}.part"]
    assert _piece(client, sid, b"efgh", 10, token, 4).json() == {"token": token, "size": 8}
    last = _piece(client, sid, b"ij", 10, token, 8)
    assert last.status_code == 201
    assert last.json() == {"token": token, "size": 10}
    assert rig.area.path(sid, token).read_bytes() == b"abcdefghij"


def test_a_piece_sent_twice_lands_once(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    token = _piece(client, sid, b"abcd", 8).json()["token"]
    _piece(client, sid, b"ef", 8, token, 4)  # half of a piece, then the drop
    assert _piece(client, sid, b"efgh", 8, token, 4).status_code == 201
    assert rig.area.path(sid, token).read_bytes() == b"abcdefgh"


def test_the_last_piece_sent_again_is_answered_landed(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    token = _piece(client, sid, b"ab", 4).json()["token"]
    assert _piece(client, sid, b"cd", 4, token, 2).status_code == 201
    again = _piece(client, sid, b"cd", 4, token, 2)
    assert again.status_code == 201
    assert again.json() == {"token": token, "size": 4}


def test_a_piece_past_what_arrived_is_told_the_size(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    token = _piece(client, sid, b"ab", 8).json()["token"]
    res = _piece(client, sid, b"gh", 8, token, 6)
    assert res.status_code == 409
    assert res.json() == {"token": token, "size": 2}


def test_a_total_over_the_cap_is_refused_before_reading(tmp_path: Path):
    r = _Rig(tmp_path / "area", cap=8)
    try:
        with TestClient(r.app) as c:
            sid = r.open_tab()
            assert _piece(c, sid, b"x", 9).status_code == 413
            assert r.files(sid) == []
    finally:
        r.area.cleanup()


def test_no_cap_by_default_takes_any_total(tmp_path: Path):
    bracket, _ = uploads(tmp_path / "area")
    assert bracket.area.cap is None
    r = _Rig(tmp_path / "area", cap=None)
    try:
        with TestClient(r.app) as c:
            sid = r.open_tab()
            # Ten TiB declared: nothing refuses it, the first piece goes in.
            answer = _piece(c, sid, b"x", 10 << 40)
            assert answer.status_code == 202
            assert answer.json()["size"] == 1
    finally:
        r.area.cleanup()


def test_a_full_disk_drops_the_part_and_says_so(rig: _Rig, client: TestClient, monkeypatch):
    import errno
    import pathlib

    real = pathlib.Path.open

    class _Full:
        def __init__(self, f) -> None:
            self.f = f

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> None:
            self.f.close()

        def seek(self, n: int) -> None:
            self.f.seek(n)

        def truncate(self) -> None:
            self.f.truncate()

        def write(self, data: bytes) -> int:
            raise OSError(errno.ENOSPC, "No space left on device")

    def opened(self, mode="r", *args, **kwargs):
        f = real(self, mode, *args, **kwargs)
        return _Full(f) if self.name.endswith(".part") else f

    monkeypatch.setattr(pathlib.Path, "open", opened)
    sid = rig.open_tab()
    answer = _piece(client, sid, b"abc", 3)
    assert answer.status_code == 507
    assert rig.files(sid) == []


def test_a_piece_running_past_its_total_is_cut(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    token = _piece(client, sid, b"ab", 4).json()["token"]
    assert _piece(client, sid, b"cdef", 4, token, 2).status_code == 400
    assert rig.files(sid) == []


def test_an_empty_file_lands_from_its_one_piece(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    res = _piece(client, sid, b"", 0)
    assert res.status_code == 201
    assert rig.area.path(sid, res.json()["token"]).read_bytes() == b""


@pytest.mark.parametrize(
    "query",
    ["total=x", "total=4&token=nope&offset=0", "total=4&token=" + "a" * 32 + "&offset=9"],
)
def test_a_bad_piece_query_is_refused(rig: _Rig, client: TestClient, query: str):
    sid = rig.open_tab()
    assert client.post(f"{_url(sid)}?{query}", content=b"ab", headers=SAME).status_code == 400


def test_a_piece_of_an_unknown_token_is_not_found(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    assert _piece(client, sid, b"ab", 4, "b" * 32, 2).status_code == 404


async def test_a_dropped_piece_keeps_what_arrived_before_it(rig: _Rig):
    sid = rig.open_tab()
    with TestClient(rig.app) as c:
        token = _piece(c, sid, b"abcd", 12).json()["token"]
    await _drive(
        rig.app,
        sid,
        [
            {"type": "http.request", "body": b"ef", "more_body": True},
            {"type": "http.disconnect"},
        ],
        query=f"token={token}&offset=4&total=12".encode(),
    )
    assert rig.files(sid) == [f"{token}.part"]
    assert (rig.area.root / sid / f"{token}.part").read_bytes()[:4] == b"abcd"


async def _drive(app: Starlette, sid: str, messages: list[dict], query: bytes = b"") -> list[dict]:
    """Run one POST through the ASGI app with a body told message by message."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": _url(sid),
        "raw_path": _url(sid).encode(),
        "query_string": query,
        "root_path": "",
        "headers": [(b"host", b"testserver"), (b"sec-fetch-site", b"same-origin")],
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
    }
    inbox = messages
    sent: list[dict] = []

    async def receive() -> dict:
        if inbox:
            return inbox.pop(0)
        await asyncio.sleep(3600)
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        sent.append(message)

    await app(scope, receive, send)
    return sent


async def test_a_broken_stream_leaves_no_file(rig: _Rig):
    sid = rig.open_tab()
    await _drive(
        rig.app,
        sid,
        [
            {"type": "http.request", "body": b"half of it", "more_body": True},
            {"type": "http.disconnect"},
        ],
    )
    assert rig.files(sid) == []


async def test_a_tab_closing_mid_stream_drops_what_landed(rig: _Rig):
    sid = rig.open_tab()

    class _CloseOnRead(list):
        def pop(self, i: int = -1) -> dict:
            message = super().pop(i)
            if not message.get("more_body"):
                rig.close_tab(sid)
            return message

    messages = _CloseOnRead(
        [
            {"type": "http.request", "body": b"one", "more_body": True},
            {"type": "http.request", "body": b"two", "more_body": False},
        ],
    )
    sent = await _drive(rig.app, sid, messages)
    assert sent[0]["status"] == 403
    assert not (rig.area.root / sid).exists() or rig.files(sid) == []


# ---- same_origin -------------------------------------------------------------


def test_same_origin_reads_fetch_metadata_first():
    class _Req:
        def __init__(self, headers: dict) -> None:
            self.headers = {k.lower(): v for k, v in headers.items()}

    assert same_origin(_Req({"Sec-Fetch-Site": "same-origin", "Host": "a"}))
    assert not same_origin(
        _Req({"Sec-Fetch-Site": "cross-site", "Origin": "http://a", "Host": "a"})
    )
    assert same_origin(_Req({"Origin": "https://Localhost:8080", "Host": "localhost:8080"}))
    assert not same_origin(_Req({"Origin": "ftp://a", "Host": "a"}))
    assert not same_origin(_Req({"Host": "a"}))


# ---- the area ----------------------------------------------------------------


def test_path_refuses_bad_tokens(rig: _Rig):
    sid = rig.open_tab()
    token, part = rig.area.new(sid)
    part.write_bytes(b"x")
    rig.area.land(sid, token)
    for bad in (
        "",
        "abc",
        token.upper(),
        token + "0",
        "../" + token[3:],
        f"{token[:-1]}g",
        None,
        7,
    ):
        with pytest.raises(ValueError, match="not an upload token"):
            rig.area.path(sid, bad)  # type: ignore[arg-type]
    with pytest.raises(FileNotFoundError):
        rig.area.path(sid, uuid.uuid4().hex)


def test_path_refuses_a_part_still_being_written(rig: _Rig):
    sid = rig.open_tab()
    token, part = rig.area.new(sid)
    part.write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        rig.area.path(sid, token)


def test_path_refuses_other_sids_and_climbing_sids(rig: _Rig):
    a, b = rig.open_tab(), rig.open_tab()
    token, part = rig.area.new(a)
    part.write_bytes(b"x")
    rig.area.land(a, token)
    assert rig.area.path(a, token).read_bytes() == b"x"
    with pytest.raises(FileNotFoundError):
        rig.area.path(b, token)
    for bad in ("..", ".", "", f"../{a}", f"{a}/..", "a b"):
        with pytest.raises(ValueError, match="not a session id"):
            rig.area.path(bad, token)


def test_path_refuses_a_symlink_out_of_the_tab_dir(rig: _Rig, tmp_path: Path):
    sid = rig.open_tab()
    outside = tmp_path / "secret"
    outside.write_bytes(b"secret")
    token = uuid.uuid4().hex
    home = rig.area.root / sid
    home.mkdir(parents=True)
    (home / token).symlink_to(outside)
    with pytest.raises(ValueError, match="outside"):
        rig.area.path(sid, token)


def test_drop_removes_one_file_and_its_part(rig: _Rig):
    sid = rig.open_tab()
    kept, part = rig.area.new(sid)
    part.write_bytes(b"k")
    rig.area.land(sid, kept)
    token, part = rig.area.new(sid)
    part.write_bytes(b"x")
    rig.area.land(sid, token)
    rig.area.drop(sid, token)
    rig.area.drop(sid, token)  # gone already is fine
    writing, part = rig.area.new(sid)
    part.write_bytes(b"w")
    rig.area.drop(sid, writing)
    assert rig.files(sid) == [kept]


def test_sweep_removes_a_tab_and_only_that_tab(rig: _Rig):
    a, b = rig.open_tab(), rig.open_tab()
    for sid in (a, b):
        token, part = rig.area.new(sid)
        part.write_bytes(b"x")
        rig.area.land(sid, token)
    rig.area.sweep(a)
    rig.area.sweep(a)
    assert not (rig.area.root / a).exists()
    assert len(rig.files(b)) == 1


def test_a_tab_closing_sweeps_its_dir(rig: _Rig, client: TestClient):
    a, b = rig.open_tab(), rig.open_tab()
    client.post(_url(a), content=b"x", headers=SAME)
    client.post(_url(b), content=b"y", headers=SAME)
    rig.close_tab(a)
    assert not (rig.area.root / a).exists()
    assert len(rig.files(b)) == 1


def test_another_tab_opening_sweeps_nothing(rig: _Rig, client: TestClient):
    a = rig.open_tab()
    client.post(_url(a), content=b"x", headers=SAME)
    rig.open_tab()
    assert len(rig.files(a)) == 1


def test_tokens_are_fresh_hex(rig: _Rig):
    sid = rig.open_tab()
    tokens = {rig.area.new(sid)[0] for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(t) == 32 and int(t, 16) >= 0 and t == t.lower() for t in tokens)


def test_setup_sweeps_stale_areas_and_leaves_fresh_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    temp = tmp_path / "tmp"
    temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    old = time.time() - STALE_AFTER - 60
    stale = temp / "nu-uploads-stale"
    (stale / "sid").mkdir(parents=True)
    os.utime(stale / "sid", (old, old))
    os.utime(stale, (old, old))
    fresh = temp / "nu-uploads-fresh"
    fresh.mkdir()
    other = temp / "not-ours"
    other.mkdir()
    os.utime(other, (old, old))

    root = temp / "area"
    root.mkdir()
    leftover = root / "deadsid"
    leftover.mkdir()
    os.utime(leftover, (old, old))
    recent = root / "livesid"
    recent.mkdir()

    rig = _Rig(root)
    assert not stale.exists()
    assert fresh.exists()
    assert other.exists()
    assert not leftover.exists()
    assert recent.exists()
    rig.area.cleanup()


def test_a_stale_area_with_a_fresh_file_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    old = time.time() - STALE_AFTER - 60
    busy = tmp_path / "nu-uploads-busy"
    (busy / "sid").mkdir(parents=True)
    os.utime(busy, (old, old))
    rig = _Rig(tmp_path / "area")
    assert busy.exists()
    rig.area.cleanup()


def test_cleanup_removes_the_root_and_stops_following(tmp_path: Path):
    rig = _Rig(tmp_path / "area")
    sid = rig.open_tab()
    token, part = rig.area.new(sid)
    part.write_bytes(b"x")
    rig.area.land(sid, token)
    rig.area.cleanup()
    assert not rig.area.root.exists()
    assert rig.server._channel._subs == []
    assert not rig.area.is_live(sid)


def test_setup_outside_a_server_says_where_it_goes(tmp_path: Path):
    _, routes = uploads(tmp_path / "area")
    del routes
    area = UploadArea(tmp_path / "area")
    with pytest.raises(LookupError, match="listen"):
        area.setup(Context())


def test_the_default_root_is_fixed_at_build_and_made_at_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    bracket, _ = uploads()
    area: UploadArea = bracket.area
    assert area.root.parent == tmp_path
    assert area.root.name.startswith("nu-uploads-")
    assert not area.root.exists()
    server = WebServer(session_cls=_Session)
    area.setup(Context().bind(WebServer, server))
    assert area.root.is_dir()
    area.cleanup()
    assert not area.root.exists()


def test_a_negative_cap_is_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="byte count"):
        uploads(tmp_path, cap=-1)


# ---- the bracket and the program side ---------------------------------------


async def test_the_bracket_binds_the_area_and_tears_it_down(tmp_path: Path):
    bracket, _ = uploads(tmp_path / "area")
    server = WebServer(session_cls=_Session)
    ctx = Context().bind(WebServer, server)
    bound, _ = await nu.arun(nu.With(bracket, body=FabricRef(UploadArea)), ctx)
    assert bound is bracket.area
    assert not bound.root.exists()


def test_the_bracket_opens_the_area_under_the_sync_runner_too(tmp_path: Path):
    bracket, _ = uploads(tmp_path / "area")
    server = WebServer(session_cls=_Session)
    ctx = Context().bind(WebServer, server)
    exists, _ = nu.run(nu.With(bracket, body=FabricRef(UploadArea).exists()), ctx)
    assert exists is True
    assert not bracket.area.root.exists()


async def test_upload_view_binds_the_tab_view(tmp_path: Path):
    bracket, _ = uploads(tmp_path / "area")
    area: UploadArea = bracket.area
    server = WebServer(session_cls=_Session)
    sid = uuid.uuid4().hex
    ctx = Context().bind(dict, {"sid": sid}, SessionId).bind(WebServer, server)
    view, _ = await nu.arun(nu.With(bracket, body=upload_view(FabricRef(UploadView))), ctx)
    assert isinstance(view, UploadView)
    assert view.sid == sid
    assert view.url == f"/_nu/upload/{sid}"
    assert view.root == area.root


async def test_upload_view_without_an_area_says_so():
    with pytest.raises(LookupError, match="UploadArea"):
        ctx = Context().bind(dict, {"sid": uuid.uuid4().hex}, SessionId)
        await nu.arun(upload_view(FabricRef(UploadView)), ctx)


def test_a_view_built_from_the_root_resolves_what_the_area_landed(rig: _Rig, client: TestClient):
    sid = rig.open_tab()
    token = client.post(_url(sid), content=b"hello", headers=SAME).json()["token"]
    view = UploadView(rig.area.root, sid)
    assert view.path(token).read_bytes() == b"hello"
    other = UploadView(rig.area.root, rig.open_tab())
    with pytest.raises(FileNotFoundError):
        other.path(token)
    view.drop(token)
    with pytest.raises(FileNotFoundError):
        view.path(token)


def test_a_view_refuses_a_climbing_sid(tmp_path: Path):
    with pytest.raises(ValueError, match="not a session id"):
        UploadView(tmp_path, "../x")


# ---- serve -------------------------------------------------------------------


def _routes_of(tree: nu.With) -> list:
    listen_bracket = tree.brackets[0]
    return list(config(listen_bracket)["kwargs"]["routes"])


def test_serve_always_mounts_the_intake(tmp_path: Path):
    tree = serve(
        nu.Str("x"), static=None, open_browser=False, upload_root=tmp_path / "up", upload_cap=7
    )
    paths = [r.path for r in _routes_of(tree)]
    assert f"{UPLOAD_PREFIX}/{{sid}}" in paths
    area = tree.brackets[1].area
    assert area.root == (tmp_path / "up").absolute()
    assert area.cap == 7


def test_serve_defaults_to_a_temp_root_and_no_cap():
    tree = serve(nu.Str("x"), static=None, open_browser=False)
    area = tree.brackets[1].area
    assert area.root.name.startswith("nu-uploads-")
    assert area.cap is None


def test_uploads_pickle_for_another_process(tmp_path):
    """The area's bracket and its route ship to a worker: no lock or handle in them pickles badly."""
    import cloudpickle

    bracket, routes = uploads(tmp_path)
    copied_bracket, copied_routes = cloudpickle.loads(cloudpickle.dumps((bracket, routes)))
    assert [r.path for r in copied_routes] == [r.path for r in routes]
    assert type(copied_bracket) is type(bracket)
