"""The upload refs: the selection, the reads, the commands and their errors.

Wire only, no browser. A fake tab answers every command the way the kit does:
it keeps the per file state (bytes, token, a running pull), writes landed and
sliced files into a real tmp area through the layout ``UploadView`` reads, and
answers with notifies on the node's path, a loop turn later, as a socket
would.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING, Any

import pytest

import nu
import nustd.ui
from nu import Context, Shape
from nu.lang.null import is_null
from nustd.ui import Column, Session
from nustd.ui.core import UploadView
from nustd.ui.refs import (
    FileGone,
    NoFile,
    Row,
    UploadCanceled,
    UploadedFileRef,
    UploadError,
    UploadFailed,
    UploadFileRef,
    UploadFilesRef,
    UploadRefused,
    UploadTooLarge,
)
from nustd.ui.refs.leaves import upload as up


if TYPE_CHECKING:
    from pathlib import Path


SID = "tab1"
ONE = ("page", "sec", "f")
MANY = ("page", "sec", "fs")


def _app():
    sec = type(
        "UpSec",
        (Row,),
        {
            "f": UploadFileRef.slot(accept=".csv", label="Orders"),
            "fs": UploadFilesRef.slot(max_files=3),
        },
    )
    page = type("UpPage", (Column,), {"sec": sec.slot()})
    return type("UpApp", (Shape,), {"page": page.slot()})


APP = _app()
F = APP.page.sec.f
FS = APP.page.sec.fs


# --- the fake tab ------------------------------------------------------------


class _Sub:
    def __init__(self, tab: _Tab, path: tuple[str, ...]) -> None:
        self.tab = tab
        self.path = path
        self.callbacks: list = []
        self.closed = False

    def bind(self, cb) -> None:
        if not self.closed and not any(c is cb for c in self.callbacks):
            self.callbacks.append(cb)

    def unbind(self, cb) -> None:
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self) -> None:
        self.closed = True
        self.callbacks = []
        self.tab.subs.remove(self)


class _File:
    def __init__(self, data: bytes, *, readable: bool = True) -> None:
        self.key = uuid.uuid4().hex[:8]
        self.data = data
        self.readable = readable
        self.token: str | None = None
        self.running: list[str] = []  # rids waiting on a pull that is held


class _Tab(Session):
    """A browser tab with upload nodes at ``ONE`` and ``MANY``.

    ``fail`` makes every transfer end with that code. ``hold`` keeps a pull
    running until ``cancel`` or ``finish``. ``value`` answers reads.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.frames: list = []
        self.subs: list[_Sub] = []
        self.nodes: dict[tuple[str, ...], list[_File]] = {ONE: [], MANY: []}
        self.fail = ""
        self.hold = False
        self.closed = False
        self.posts = 0
        self.value: Any = None

    # Session ---------------------------------------------------------------

    async def send(self, frame) -> None:
        if self.closed:
            raise RuntimeError("Cannot call send once a close message has been sent")
        self.frames.append(frame)
        asyncio.get_running_loop().call_soon(self._handle, frame)

    async def aread(self, path):
        return self.value

    def subscribe(self, path):
        sub = _Sub(self, tuple(path))
        self.subs.append(sub)
        return sub

    # the browser -----------------------------------------------------------

    def notify(self, path, payload) -> None:
        for sub in tuple(self.subs):
            if sub.path == tuple(path):
                for cb in tuple(sub.callbacks):
                    cb(payload)

    def _targets(self, path, key) -> list[_File]:
        files = self.nodes[path]
        if key is None:
            return files[:1] if path == ONE else list(files)
        return [files[key]] if isinstance(key, int) and key < len(files) else []

    def _land(self, data: bytes) -> str:
        token = uuid.uuid4().hex
        home = self.root / SID
        home.mkdir(parents=True, exist_ok=True)
        (home / token).write_bytes(data)
        self.posts += 1
        return token

    def _landed(self, f: _File) -> bool:
        return f.token is not None and (self.root / SID / f.token).exists()

    def _handle(self, frame) -> None:
        path, p = frame.ref, frame.payload
        targets = self._targets(path, p.get("key"))
        if frame.op == "pull":
            if not targets:
                self.notify(path, _up(p, None, "failed", 0, "no_file"))
            for f in targets:
                self.pull(path, f, p["rid"])
        elif frame.op == "slice":
            if not targets:
                self.notify(path, _sl(p, None, False, "picked", 0, "no_file"))
                return
            f = targets[0]
            if self._landed(f):
                self.notify(path, _sl(p, f.token, True, "landed", len(f.data), "", f.key))
            elif self.fail or not f.readable:
                code = self.fail or "unreadable"
                self.notify(path, _sl(p, None, False, "failed", len(f.data), code, f.key))
            else:
                part = f.data[p["start"] : p["end"]]
                token = self._land(part)
                self.notify(path, _sl(p, token, False, "picked", len(f.data), "", f.key))
        elif frame.op == "cancel":
            for f in targets:
                for rid in f.running:
                    self.notify(
                        path, _up({"rid": rid}, None, "canceled", len(f.data), "canceled", f.key)
                    )
                f.running = []
        elif frame.op == "discard":
            f = targets[0] if targets else None
            token = f.token if f else None
            if f:
                f.token = None
            self.notify(
                path,
                {"event": "discard", "key": f.key if f else None, "rid": p["rid"], "token": token},
            )
        elif frame.op == "remove_file":
            for f in targets:
                self.nodes[path].remove(f)
            self.notify(path, {"event": "change"})

    def pull(self, path, f: _File, rid: str) -> None:
        if self._landed(f):
            self.notify(path, _up({"rid": rid}, f.token, "landed", len(f.data), "", f.key))
            return
        if f.running or self.hold:
            f.running.append(rid)
            return
        if self.fail or not f.readable:
            code = self.fail or "unreadable"
            self.notify(path, _up({"rid": rid}, None, "failed", len(f.data), code, f.key))
            return
        self.notify(
            path,
            {
                "event": "progress",
                "key": f.key,
                "rid": rid,
                "sent": len(f.data),
                "size": len(f.data),
            },
        )
        f.token = self._land(f.data)
        self.notify(path, _up({"rid": rid}, f.token, "landed", len(f.data), "", f.key))

    def finish(self, path) -> None:
        """Land every held pull on ``path``, answering each waiting rid."""
        for f in self.nodes[path]:
            rids, f.running = f.running, []
            if rids:
                f.token = self._land(f.data)
            for rid in rids:
                self.notify(path, _up({"rid": rid}, f.token, "landed", len(f.data), "", f.key))

    def ops(self) -> list[tuple[str, tuple[str, ...], Any]]:
        return [(f.op, f.ref, f.payload) for f in self.frames]

    def tab_files(self) -> list[str]:
        home = self.root / SID
        return sorted(p.name for p in home.iterdir()) if home.exists() else []


def _up(p, token, state, size, error, key=None) -> dict:
    return {
        "event": "upload",
        "key": key,
        "rid": p["rid"],
        "token": token,
        "state": state,
        "size": size,
        "error": error,
    }


def _sl(p, token, cached, state, size, error, key=None) -> dict:
    return {
        "event": "slice",
        "key": key,
        "rid": p["rid"],
        "token": token,
        "cached": cached,
        "state": state,
        "size": size,
        "error": error,
    }


@pytest.fixture
def tab(tmp_path: Path) -> _Tab:
    return _Tab(tmp_path / "area")


def _ctx(tab: _Tab) -> Context:
    return Context().bind(Session, tab).bind(UploadView, UploadView(tab.root, SID))


def _run(tab: _Tab, term) -> Any:
    out, _ = asyncio.run(nu.arun(term, _ctx(tab)))
    return out


def _collect(tab: _Tab, stream) -> list[bytes]:
    return _run(tab, nu.Collect(stream))


def _pick(tab: _Tab, data: bytes, path=ONE, **kw) -> _File:
    f = _File(data, **kw)
    tab.nodes[path].append(f)
    return f


DATA = bytes(range(256)) * 40  # 10240 bytes


# --- slot, value, set, reset -------------------------------------------------


def test_slot_props_follow_the_contract():
    assert UploadFileRef.slot().props == {
        "accept": "",
        "max_size": None,
        "prompt": "",
        "label": "",
        "disabled": False,
        "readonly": False,
        "required": False,
        "autofocus": False,
        "size": "md",
    }
    props = UploadFilesRef.slot(accept="image/*", max_size=10, max_files=2, prompt="Drop").props
    assert props["accept"] == "image/*"
    assert props["max_size"] == 10
    assert props["max_files"] == 2
    assert props["prompt"] == "Drop"
    assert "value" not in props


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "1"])
def test_slot_refuses_a_bad_limit(bad):
    with pytest.raises(ValueError, match="max_size"):
        UploadFileRef.slot(max_size=bad)
    with pytest.raises(ValueError, match="max_files"):
        UploadFilesRef.slot(max_files=bad)


def test_slot_takes_no_value_seed():
    with pytest.raises(TypeError):
        UploadFileRef.slot(value={"name": "x"})


def test_set_raises_when_the_tree_is_built():
    with pytest.raises(TypeError, match="cannot put a file in a picker"):
        F.set({"name": "a.csv"})
    with pytest.raises(TypeError, match="cannot put a file in a picker"):
        FS.set([])


def test_value_is_the_selection_or_null(tab):
    picked = {"key": "k1", "name": "a.csv", "mime": "text/csv", "size": 3, "modified": 1}
    tab.value = picked
    assert _run(tab, F) == picked
    tab.value = None
    assert is_null(_run(tab, F))


def test_files_value_is_a_list_and_empty_reads_empty(tab):
    tab.value = None
    assert _run(tab, FS) == []
    tab.value = [{"key": "a"}, {"key": "b"}]
    assert _run(tab, FS) == [{"key": "a"}, {"key": "b"}]


def test_reset_clears_with_the_chain(tab):
    _run(tab, F.reset())
    [frame] = tab.frames
    assert frame.op == "reset"
    assert frame.ref == ONE
    assert frame.chain[-1][1] == "UploadFileRef"


def test_setters_write_one_prop(tab):
    _run(tab, F.set_accept(".tsv") >> F.set_prompt("Drop a table") >> F.set_max_size(5))
    _run(tab, FS.set_max_files(4))
    assert [(f.op, f.payload) for f in tab.frames] == [
        ("write", {"accept": ".tsv"}),
        ("write", {"prompt": "Drop a table"}),
        ("write", {"max_size": 5}),
        ("write", {"max_files": 4}),
    ]


def test_command_ops_are_the_class_names():
    assert [c.op() for c in (up.Pull, up.Slice, up.Cancel, up.Discard, up.RemoveFile)] == [
        "pull",
        "slice",
        "cancel",
        "discard",
        "remove_file",
    ]


# --- get_slice / get_bytes ---------------------------------------------------


def test_get_slice_uncached_reads_the_slice_file_and_deletes_it(tab):
    _pick(tab, DATA)
    assert _run(tab, F.get_slice(10, 20)) == DATA[10:20]
    [(op, ref, payload)] = tab.ops()
    assert (op, ref) == ("slice", ONE)
    assert payload["key"] is None
    assert payload["url"] == f"/_nu/upload/{SID}"
    assert (payload["start"], payload["end"]) == (10, 20)
    assert len(payload["rid"]) == 32
    assert tab.posts == 1
    assert tab.tab_files() == []


def test_get_slice_ships_the_chain_so_the_node_can_be_made(tab):
    _pick(tab, DATA)
    _run(tab, F.get_slice(0, 1))
    assert [seg for seg, _, _ in tab.frames[0].chain] == list(ONE)
    assert tab.frames[0].chain[-1][1] == "UploadFileRef"


def test_get_slice_open_end_sends_null(tab):
    _pick(tab, DATA)
    assert _run(tab, F.get_slice(10_000)) == DATA[10_000:]
    assert tab.frames[0].payload["end"] is None


def test_get_slice_cached_reads_the_range_and_keeps_the_cache(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull())
    posts = tab.posts
    assert _run(tab, F.get_slice(100, 200)) == DATA[100:200]
    assert _run(tab, F.get_slice(-16)) == DATA[-16:]
    assert _run(tab, F.get_slice(5, 2)) == b""
    assert _run(tab, F.get_slice(10_000, 99_999)) == DATA[10_000:]
    assert tab.posts == posts
    assert tab.tab_files() == [f.token]


def test_get_bytes_reads_the_whole_file(tab):
    _pick(tab, DATA)
    assert _run(tab, F.get_bytes()) == DATA
    assert tab.frames[0].payload["start"] == 0
    assert tab.frames[0].payload["end"] is None
    assert tab.tab_files() == []


def test_get_bytes_cached(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull())
    assert _run(tab, F.get_bytes()) == DATA
    assert tab.tab_files() == [f.token]


def test_get_bytes_warns_past_the_threshold(tab, caplog, monkeypatch):
    monkeypatch.setattr(up, "GET_BYTES_WARN", 1000)
    _pick(tab, DATA)
    with caplog.at_level(logging.WARNING, logger=up.__name__):
        assert _run(tab, F.get_bytes()) == DATA
    [record] = caplog.records
    message = record.getMessage()
    assert "page/sec/f" in message
    assert str(len(DATA)) in message
    assert "open()" in message


def test_get_bytes_under_the_threshold_is_quiet(tab, caplog):
    _pick(tab, DATA)
    with caplog.at_level(logging.WARNING, logger=up.__name__):
        _run(tab, F.get_bytes())
    assert caplog.records == []


def test_get_slice_refuses_a_non_int_bound(tab):
    _pick(tab, DATA)
    with pytest.raises(TypeError, match="start"):
        _run(tab, F.get_slice("0", 4))


# --- open --------------------------------------------------------------------


def test_open_pulls_then_reads_the_cache_in_pieces(tab):
    f = _pick(tab, DATA)
    pieces = _collect(tab, F.open(step=4096))
    assert [len(p) for p in pieces] == [4096, 4096, 2048]
    assert b"".join(pieces) == DATA
    assert [op for op, _, _ in tab.ops()] == ["pull"]
    assert tab.tab_files() == [f.token]


def test_open_takes_a_range(tab):
    _pick(tab, DATA)
    pieces = _collect(tab, F.open(100, 1100, step=300))
    assert [len(p) for p in pieces] == [300, 300, 300, 100]
    assert b"".join(pieces) == DATA[100:1100]
    assert b"".join(_collect(tab, F.open(-10))) == DATA[-10:]


def test_open_on_a_landed_file_posts_nothing_new(tab):
    _pick(tab, DATA)
    _run(tab, F.pull())
    assert tab.posts == 1
    assert b"".join(_collect(tab, F.open())) == DATA
    assert tab.posts == 1


def test_open_refuses_a_step_that_never_moves(tab):
    _pick(tab, DATA)
    with pytest.raises(ValueError, match="step"):
        _collect(tab, F.open(step=0))


# --- pull, cancel, discard ---------------------------------------------------


def test_pull_returns_at_once_with_key_rid_url(tab):
    _pick(tab, DATA)
    _run(tab, F.pull())
    [(op, ref, payload)] = tab.ops()
    assert (op, ref) == ("pull", ONE)
    assert set(payload) == {"key", "rid", "url"}
    assert payload["key"] is None


def test_pull_twice_lands_once(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull() >> F.pull())
    rids = [p["rid"] for _, _, p in tab.ops()]
    assert len(rids) == 2
    assert rids[0] != rids[1]
    assert tab.posts == 1
    assert tab.tab_files() == [f.token]


def test_cancel_raises_in_a_waiting_read(tab):
    _pick(tab, DATA)
    tab.hold = True

    async def run():
        ctx = _ctx(tab)
        reading = asyncio.create_task(nu.arun(nu.Collect(F.open()), ctx))
        for _ in range(200):
            if any(op == "pull" for op, _, _ in tab.ops()):
                break
            await asyncio.sleep(0.01)
        await nu.arun(F.cancel(), ctx)
        with pytest.raises(UploadCanceled):
            await reading

    asyncio.run(run())
    assert [(op, p) for op, _, p in tab.ops()][-1] == ("cancel", {"key": None})
    assert tab.subs == []


def test_a_held_pull_answers_every_waiting_read(tab):
    _pick(tab, DATA)
    tab.hold = True

    async def run():
        ctx = _ctx(tab)
        a = asyncio.create_task(nu.arun(nu.Collect(F.open()), ctx))
        b = asyncio.create_task(nu.arun(nu.Collect(F.open(0, 10)), ctx))
        for _ in range(200):
            if sum(op == "pull" for op, _, _ in tab.ops()) == 2:
                break
            await asyncio.sleep(0.01)
        tab.finish(ONE)
        return (await a)[0], (await b)[0]

    whole, head = asyncio.run(run())
    assert b"".join(whole) == DATA
    assert b"".join(head) == DATA[:10]


def test_discard_drops_the_cache_and_keeps_the_selection(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull())
    token = f.token
    assert tab.tab_files() == [token]
    _run(tab, F.discard())
    assert tab.tab_files() == []
    op, ref, payload = tab.ops()[-1]
    assert (op, ref) == ("discard", ONE)
    assert set(payload) == {"key", "rid"}
    assert tab.nodes[ONE] == [f]
    # the next read pulls again, and returns the same bytes
    assert b"".join(_collect(tab, F.open())) == DATA
    assert tab.posts == 2


def test_discard_with_nothing_landed_is_fine(tab):
    _pick(tab, DATA)
    _run(tab, F.discard())
    assert tab.tab_files() == []


# --- errors ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "error"),
    [
        ("unreadable", FileGone),
        ("canceled", UploadCanceled),
        ("too_large", UploadTooLarge),
        ("refused", UploadRefused),
        ("network", UploadFailed),
    ],
)
def test_every_code_raises_its_error(tab, code, error):
    _pick(tab, DATA)
    tab.fail = code
    with pytest.raises(error) as slice_err:
        _run(tab, F.get_slice(0, 4))
    with pytest.raises(error):
        _collect(tab, F.open())
    assert isinstance(slice_err.value, UploadError)
    assert slice_err.value.code == code
    assert "page/sec/f" in str(slice_err.value)


def test_an_empty_input_raises_no_file_on_every_read(tab):
    for term in (F.get_slice(0, 4), F.get_bytes(), nu.Collect(F.open())):
        with pytest.raises(NoFile, match="no file is picked"):
            _run(tab, term)


def test_a_file_changed_on_disk_raises_file_gone(tab):
    _pick(tab, DATA, readable=False)
    with pytest.raises(FileGone, match="pick it again"):
        _run(tab, F.get_bytes())


def test_too_large_names_the_cap_side(tab):
    _pick(tab, DATA)
    tab.fail = "too_large"
    with pytest.raises(UploadTooLarge, match="cap"):
        _run(tab, F.get_bytes())


def test_an_unknown_code_is_a_failed_upload(tab):
    _pick(tab, DATA)
    tab.fail = "teapot"
    with pytest.raises(UploadFailed, match="teapot"):
        _run(tab, F.get_bytes())


def test_a_token_that_names_nothing_is_refused(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull())
    (tab.root / SID / f.token).unlink()
    tab._landed = lambda f: f.token is not None  # the tab still thinks it landed
    with pytest.raises(UploadRefused):
        _run(tab, F.get_slice(0, 4))
    with pytest.raises(UploadRefused):
        _collect(tab, F.open())


def test_a_malformed_token_is_refused(tab):
    f = _pick(tab, DATA)
    _run(tab, F.pull())
    f.token = "../../etc/passwd"  # noqa: S105 - a path, not a secret
    tab._landed = lambda f: True
    with pytest.raises(UploadRefused):
        _run(tab, F.get_bytes())


# --- the session ending ------------------------------------------------------


def test_a_closed_session_raises_connection_error(tab):
    _pick(tab, DATA)
    tab.closed = True
    with pytest.raises(ConnectionError):
        _run(tab, F.get_slice(0, 4))
    assert tab.subs == []


def test_the_tab_closing_mid_wait_unsubscribes(tab):
    """A closed tab cancels its arm: the waiting read ends and leaves no subscription."""
    _pick(tab, DATA)
    tab.hold = True

    async def run():
        reading = asyncio.create_task(nu.arun(nu.Collect(F.open()), _ctx(tab)))
        for _ in range(200):
            if tab.frames:
                break
            await asyncio.sleep(0.01)
        assert len(tab.subs) == 1
        tab.closed = True
        reading.cancel()
        with pytest.raises(asyncio.CancelledError):
            await reading

    asyncio.run(run())
    assert tab.subs == []


def test_a_read_with_no_upload_view_says_who_binds_it(tab):
    _pick(tab, DATA)
    with pytest.raises(LookupError, match="UploadView"):
        asyncio.run(nu.arun(F.get_bytes(), Context().bind(Session, tab)))


def test_reads_ignore_answers_for_other_requests(tab):
    """Two reads at once: each takes only the notify with its own rid."""
    _pick(tab, DATA)

    async def run():
        ctx = _ctx(tab)
        a = nu.arun(F.get_slice(0, 3), ctx)
        b = nu.arun(F.get_slice(3, 6), ctx)
        (x, _), (y, _) = await asyncio.gather(a, b)
        return x, y

    assert asyncio.run(run()) == (DATA[0:3], DATA[3:6])


# --- UploadFilesRef ----------------------------------------------------------


def test_file_i_reads_one_entry_by_index_on_the_files_node(tab):
    _pick(tab, b"first", MANY)
    _pick(tab, DATA, MANY)
    assert _run(tab, FS.file(1).get_slice(0, 8)) == DATA[:8]
    assert _run(tab, FS.file(0).get_bytes()) == b"first"
    (op, ref, payload), _ = tab.ops()
    assert (op, ref) == ("slice", MANY)
    assert payload["key"] == 1
    assert tab.frames[0].chain[-1][:2] == ("fs", "UploadFilesRef")


def test_file_i_open_and_discard(tab):
    _pick(tab, b"first", MANY)
    second = _pick(tab, DATA, MANY)
    assert b"".join(_collect(tab, FS.file(1).open(step=1000))) == DATA
    assert tab.tab_files() == [second.token]
    _run(tab, FS.file(1).discard())
    assert tab.tab_files() == []
    assert [(op, p["key"]) for op, _, p in tab.ops()] == [("pull", 1), ("discard", 1)]


def test_file_i_takes_a_computed_index(tab):
    _pick(tab, b"a", MANY)
    _pick(tab, b"b", MANY)
    assert _run(tab, FS.file(nu.Int(0) + 1).get_bytes()) == b"b"


def test_file_i_past_the_selection_raises_no_file(tab):
    _pick(tab, b"a", MANY)
    with pytest.raises(NoFile, match=r"page/sec/fs\.file\(4\)"):
        _run(tab, FS.file(4).get_bytes())


def test_file_i_is_an_entry_ref():
    entry = FS.file(0)
    assert isinstance(entry, UploadedFileRef)
    assert isinstance(entry, nustd.ui.ItemRef)


@pytest.mark.parametrize("bad", [-1, "k", None, True, 1.0])
def test_file_takes_a_position(bad):
    with pytest.raises((TypeError, IndexError)):
        FS.file(bad)


def test_the_files_ref_holds_no_other_children():
    with pytest.raises(TypeError, match=r"\.file"):
        nustd.ui.TextRef("x", parent_ref=FS)


def test_an_entry_holds_no_children():
    with pytest.raises(TypeError):
        nustd.ui.TextRef("x", parent_ref=FS.file(0))


def test_reading_an_entry_itself_points_at_the_reads(tab):
    with pytest.raises(TypeError, match="get_slice"):
        _run(tab, FS.file(0))


def test_pull_and_cancel_all_name_no_key(tab):
    _pick(tab, b"a", MANY)
    _pick(tab, b"b", MANY)
    _run(tab, FS.pull() >> FS.cancel())
    assert [(op, ref, p["key"]) for op, ref, p in tab.ops()] == [
        ("pull", MANY, None),
        ("cancel", MANY, None),
    ]
    assert tab.posts == 2


def test_remove_sends_the_index(tab):
    _pick(tab, b"a", MANY)
    kept = _pick(tab, b"b", MANY)
    _run(tab, FS.remove(0))
    assert tab.ops() == [("remove_file", MANY, {"key": 0})]
    assert tab.nodes[MANY] == [kept]


async def _hear(ctx: Context, reaction, heard: list) -> None:
    """Bind a plain callback to what ``reaction`` resolves to, as ReactEvery does."""
    sub, _ = await nu.arun(reaction, ctx)
    sub.bind(heard.append)


async def _settle(check) -> None:
    for _ in range(200):
        if check():
            return
        await asyncio.sleep(0.01)


def test_per_file_reactions_carry_the_key(tab):
    a = _pick(tab, b"aaaa", MANY)
    b = _pick(tab, b"bb", MANY)
    uploads: list[dict] = []
    progress: list[dict] = []

    async def run():
        ctx = _ctx(tab)
        await _hear(ctx, FS.on_upload(), uploads)
        await _hear(ctx, FS.on_progress(), progress)
        await nu.arun(FS.pull(), ctx)
        await _settle(lambda: len(uploads) == 2)

    asyncio.run(run())
    assert sorted((ev["key"], ev["state"]) for ev in uploads) == sorted(
        [(a.key, "landed"), (b.key, "landed")]
    )
    assert {ev["event"] for ev in uploads} == {"upload"}
    assert sorted(ev["key"] for ev in progress) == sorted([a.key, b.key])
    assert {ev["event"] for ev in progress} == {"progress"}


def test_reactions_hear_their_event_only(tab):
    _pick(tab, DATA)
    uploads: list[dict] = []
    changes: list[dict] = []

    async def run():
        ctx = _ctx(tab)
        await _hear(ctx, F.on_upload(), uploads)
        await _hear(ctx, F.on_change(), changes)
        await nu.arun(F.pull(), ctx)
        await _settle(lambda: uploads)
        tab.notify(ONE, {"event": "change"})

    asyncio.run(run())
    assert [ev["event"] for ev in uploads] == ["upload"]
    assert uploads[0]["token"] == tab.nodes[ONE][0].token
    assert changes == [{"event": "change"}]


def test_errors_are_exported_from_nustd_ui():
    for name in (
        "UploadError",
        "NoFile",
        "FileGone",
        "UploadCanceled",
        "UploadTooLarge",
        "UploadRefused",
        "UploadFailed",
        "UploadFileRef",
        "UploadFilesRef",
        "UploadedFileRef",
    ):
        assert getattr(nustd.ui, name) is getattr(up, name)
        assert name in nustd.ui.__all__
    for cls in (NoFile, FileGone, UploadCanceled, UploadTooLarge, UploadRefused, UploadFailed):
        assert issubclass(cls, UploadError)
