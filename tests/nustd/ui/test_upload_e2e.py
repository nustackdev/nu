"""Upload refs end to end: a real server, a tab speaking the wire, real POSTs.

The unit suites prove each half against a fake of the other: the refs
against a scripted session (``test_upload_refs``), the intake against a
server that never starts (``test_upload_intake``), the kit in jsdom. This
one puts the python halves together for real: ``nudle.serve`` on a port,
a ws client playing the browser tab (the kit's answers, from its frame
table), and every byte POSTed over http to the intake, as the kit does.
What it checks is the round trip a person's pick takes: an uncached slice,
a pull, a cached slice, ``open`` in pieces, the file streamed into a blob
store, ``discard``, then the tab's dir swept on close and the root removed
when the server stops.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
from typing import TYPE_CHECKING, Any

import httpx
import msgpack
import pytest
from websockets.asyncio.client import connect

import nu
import nustd
from nustd import ui


if TYPE_CHECKING:
    from pathlib import Path


pytestmark = pytest.mark.timeout(30)

CSV = b"id,name\n1,ada\n2,linus\n3,grace\n"


class Page(ui.Column):
    csv = ui.UploadFileRef.slot(accept=".csv")
    many = ui.UploadFilesRef.slot()
    log = ui.ListRef.slot()


class App(nu.Shape):
    page = Page.slot()


CSV_REF = App.page.csv
MANY = App.page.many
LOG = App.page.log
Media = nustd.blob.StoreRef("media")

CSV_PATH = ["page", "csv"]
MANY_PATH = ["page", "many"]
LOG_PATH = ["page", "log"]


def _text(label: str, raw: nu.Nu) -> nu.Nu:
    return LOG.append(label + " " + nu.Bytes(raw).decode())


def _one_file() -> nu.Nu:
    """The steps a csv app takes on a pick, each logged to the list."""
    return (
        nu.let(CSV_REF.slice(0, 7), lambda head: _text("head", head))
        >> CSV_REF.pull()
        >> nu.let(
            nu.Collect(CSV_REF.open(step=8)),
            lambda pieces: LOG.append(
                "open " + nu.str(nu.List(pieces).len()) + " " + nu.Bytes(b"").join(pieces).decode()
            ),
        )
        >> nu.let(Media.put_stream(CSV_REF.open(step=8)), lambda bid: _text("blob", Media.get(bid)))
        >> nu.let(CSV_REF.slice(-6), lambda tail: _text("tail", tail))
        >> CSV_REF.discard()
        >> nu.let(CSV_REF.slice(0, 2), lambda again: _text("again", again))
        >> LOG.append("done")
    )


def _many_files() -> nu.Nu:
    """Entries by position: a slice of the second, a remove, the new first."""
    return (
        nu.let(MANY.file(1).slice(0, 3), lambda b: _text("second", b))
        >> MANY.remove(0)
        >> nu.let(MANY.file(0).bytes(), lambda b: _text("first", b))
        >> LOG.append("done")
    )


# The last arm says the reactions are listening, so the tab picks after it.
PROGRAM = ui.boot(App.page) >> nu.ParallelAsync(
    nu.ReactEvery(CSV_REF.on_change(), lambda _: _one_file()),
    nu.ReactEvery(MANY.on_change(), lambda _: _many_files()),
    LOG.append("ready"),
)


# --- the tab ------------------------------------------------------------------


class _Handle:
    def __init__(self, key: str, name: str, data: bytes) -> None:
        self.key = key
        self.name = name
        self.data = data
        self.token: str | None = None
        self.state = "picked"
        self.pulling: asyncio.Task | None = None
        self.waiters: list[str] = []

    def value(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "mime": "text/csv",
            "size": len(self.data),
            "modified": 0,
            "state": self.state,
            "sent": len(self.data) if self.state == "landed" else 0,
            "error": "",
        }


class Tab:
    """The browser tab: answers reads and upload commands as the kit does.

    The kit's frame table, in python: a pull of a landed file answers at
    once, of a running one waits with it; a slice of a landed file answers
    ``cached: true`` with no POST, else POSTs just the range. Every POST is
    recorded with its size, and every answer with what was on disk then.
    """

    def __init__(self, base: str, root: Path) -> None:
        self.base = base
        self.root = root
        self.books: dict[tuple[str, ...], list[_Handle]] = {}
        self.writes: list[tuple[list[str], str, object]] = []
        self.posts: list[int] = []
        self.answers: list[dict[str, Any]] = []
        self.on_disk: dict[str, bool] = {}
        self.sid = ""
        self._http = httpx.AsyncClient(base_url=base)
        self._tasks: set[asyncio.Task] = set()

    async def __aenter__(self) -> Tab:
        self.ws = await connect(self.base.replace("http", "ws") + "/ws")
        self._reader = asyncio.create_task(self._read())
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
        await self._http.aclose()

    async def close(self) -> None:
        await self.ws.close()
        self._reader.cancel()
        for task in (self._reader, *self._tasks):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    # --- a person's hands

    async def pick(self, path: list[str], files: list[tuple[str, bytes]]) -> None:
        await self.logged("ready")
        book = self.books.setdefault(tuple(path), [])
        for name, data in files:
            book.append(_Handle(f"f{len(book)}{name}", name, data))
        await self._send("notify", path, {"event": "change"})

    async def logged(self, until: str = "done") -> list[str]:
        """The lines the program appended to its log, once ``until`` is among them."""
        while True:
            lines = [str(p) for ref, op, p in self.writes if op == "append" and ref == LOG_PATH]
            if until in lines:
                return lines
            await asyncio.sleep(0.01)

    # --- the wire

    async def _send(self, op: str, ref: list[str], payload: object, rid: str | None = None) -> None:
        frame: dict[str, Any] = {"op": op, "ref": ref, "payload": payload}
        if rid is not None:
            frame["id"] = rid
        await self.ws.send(msgpack.packb(frame, use_bin_type=True))

    async def _read(self) -> None:
        async for raw in self.ws:
            frame = msgpack.unpackb(raw, raw=False)
            op, ref, payload = frame["op"], list(frame.get("ref") or ()), frame.get("payload")
            self.writes.append((ref, op, payload))
            book = self.books.get(tuple(ref))
            if op == "read":
                await self._send("read", ref, self._value(ref), rid=frame.get("id"))
            elif book is not None and op in ("pull", "slice", "discard", "remove_file"):
                task = asyncio.create_task(getattr(self, f"_{op}")(ref, book, payload))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

    def _value(self, ref: list[str]) -> object:
        book = self.books.get(tuple(ref))
        if ref == MANY_PATH:
            return [h.value() for h in book or ()]
        return book[0].value() if book else None

    def _find(self, book: list[_Handle], key: object) -> _Handle | None:
        if isinstance(key, int):
            return book[key] if -len(book) <= key < len(book) else None
        if key is None:
            return book[0] if book else None
        return next((h for h in book if h.key == key), None)

    async def _post(self, url: str, body: bytes) -> str:
        self.sid = url.rsplit("/", 1)[-1]
        res = await self._http.post(url, content=body, headers={"Sec-Fetch-Site": "same-origin"})
        assert res.status_code == 201, res.text
        self.posts.append(len(body))
        return res.json()["token"]

    def _exists(self, token: str | None) -> bool:
        return token is not None and (self.root / self.sid / token).is_file()

    async def _answer(self, ref: list[str], payload: dict[str, Any]) -> None:
        self.answers.append(payload)
        await self._send("notify", ref, payload)

    async def _pull(self, ref: list[str], book: list[_Handle], p: dict) -> None:
        h = self._find(book, p["key"])
        assert h is not None
        if h.state == "landed":
            await self._landed(ref, h, [p["rid"]])
            return
        h.waiters.append(p["rid"])
        if h.pulling is None:
            h.state = "pulling"
            h.pulling = asyncio.current_task()
            h.token = await self._post(p["url"], h.data)
            h.state, h.pulling = "landed", None
            self.on_disk[f"landed {h.token}"] = self._exists(h.token)
            waiters, h.waiters = h.waiters, []
            await self._landed(ref, h, waiters)

    async def _landed(self, ref: list[str], h: _Handle, rids: list[str]) -> None:
        for rid in rids:
            await self._answer(
                ref,
                {
                    "event": "upload",
                    "key": h.key,
                    "rid": rid,
                    "token": h.token,
                    "state": "landed",
                    "size": len(h.data),
                    "error": "",
                },
            )

    async def _slice(self, ref: list[str], book: list[_Handle], p: dict) -> None:
        h = self._find(book, p["key"])
        assert h is not None
        lo, hi, _ = slice(p["start"], p["end"]).indices(len(h.data))
        cached = h.state == "landed"
        token = h.token if cached else await self._post(p["url"], h.data[lo:hi])
        await self._answer(
            ref,
            {
                "event": "slice",
                "key": h.key,
                "rid": p["rid"],
                "token": token,
                "cached": cached,
                "state": "landed",
                "size": max(hi - lo, 0),
                "error": "",
            },
        )

    async def _discard(self, ref: list[str], book: list[_Handle], p: dict) -> None:
        h = self._find(book, p["key"])
        assert h is not None
        token, h.token, h.state = h.token, None, "picked"
        self.on_disk[f"discard {token}"] = self._exists(token)
        await self._answer(ref, {"event": "discard", "key": h.key, "rid": p["rid"], "token": token})

    async def _remove_file(self, ref: list[str], book: list[_Handle], p: dict) -> None:
        h = self._find(book, p["key"])
        if h is not None:
            book.remove(h)


# --- the server ---------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def server(tmp_path: Path):
    """``nudle.serve`` on a free port, its upload root under ``tmp_path``."""
    port = _free_port()
    root = tmp_path / "uploads"
    program = nu.With(nustd.blob.lmdb(Media, tmp_path / "media"), body=PROGRAM)
    app = ui.serve(program, static=None, upload_root=root, port=port, open_browser=False)
    task = asyncio.create_task(nu.arun(app))
    base = f"http://127.0.0.1:{port}"
    while not root.is_dir():
        if task.done():
            task.result()
        await asyncio.sleep(0.02)
    yield base, root, task
    if not task.done():
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def _until(check: Any) -> None:
    while not check():
        await asyncio.sleep(0.02)


# --- tests --------------------------------------------------------------------


async def test_one_file_round_trip(server: tuple[str, Path, asyncio.Task]) -> None:
    base, root, task = server
    async with Tab(base, root) as tab:
        await tab.pick(CSV_PATH, [("people.csv", CSV)])
        lines = await tab.logged()

        # what the program read, in order: every read returns the same bytes,
        # wherever they came from
        assert lines == [
            "ready",
            "head id,name",
            f"open 4 {CSV.decode()}",
            f"blob {CSV.decode()}",
            "tail grace\n",
            "again id",
            "done",
        ]
        # three POSTs: the head slice, the whole file once, the slice after
        # the discard; the cached slice, open and the blob put sent nothing
        assert tab.posts == [7, len(CSV), 2]
        slices = [a for a in tab.answers if a["event"] == "slice"]
        assert [s["cached"] for s in slices] == [False, True, False]
        # the pull and each open's own pull answered with one landed token
        uploads = [a for a in tab.answers if a["event"] == "upload"]
        assert len(uploads) == 3
        assert len({a["token"] for a in uploads}) == 1
        landed = uploads[0]["token"]
        # the cache was on disk when it landed and when it was discarded;
        # after, nothing is left: slices read and deleted, the cache dropped
        assert tab.on_disk == {f"landed {landed}": True, f"discard {landed}": True}
        tab_dir = root / tab.sid
        assert tab_dir.is_dir()
        assert list(tab_dir.iterdir()) == []

        # a cross-site POST to the same live tab never reaches the area
        res = await tab._http.post(
            f"/_nu/upload/{tab.sid}", content=b"x", headers={"Sec-Fetch-Site": "cross-site"}
        )
        assert res.status_code == 403

        # a file landed and never discarded, for the sweep below
        await tab._post(f"/_nu/upload/{tab.sid}", CSV)
        assert len(list(tab_dir.iterdir())) == 1

    # the tab closed: its dir is swept
    await _until(lambda: not tab_dir.exists())
    assert root.is_dir()

    # the server stops: the root goes with it
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    assert not root.exists()


async def test_files_by_position(server: tuple[str, Path, asyncio.Task]) -> None:
    base, root, _ = server
    async with Tab(base, root) as tab:
        await tab.pick(MANY_PATH, [("a.txt", b"alpha"), ("b.txt", b"bravo")])
        lines = await tab.logged()

        # file(1) before the remove is b.txt; file(0) after it is b.txt too
        assert lines == ["ready", "second bra", "first bravo", "done"]
        assert [h.name for h in tab.books[tuple(MANY_PATH)]] == ["b.txt"]
        # commands named entries by index on the files node itself
        keys = [p["key"] for ref, op, p in tab.writes if op in ("slice", "remove_file")]
        assert keys == [1, 0, 0]
        assert all(ref == MANY_PATH for ref, op, _ in tab.writes if op in ("slice", "remove_file"))
        assert list((root / tab.sid).iterdir()) == []
