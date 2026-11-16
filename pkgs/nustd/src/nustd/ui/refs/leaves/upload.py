"""Upload inputs: a file the person hands over, read by the program on demand.

A picked file is a handle in the browser tab, never bytes on the server. The
program decides if, when and how much of it moves: a slice to sniff a header,
the whole file to keep, nothing at all for a name to show. So the value of an
upload input is the selection only (name, size, state), and every byte read
is an interaction on the ref.

Bytes never ride the ws. A read sends a small command to the tab, the tab
POSTs the bytes to the intake (``nustd.ui.nudle.uploads``) into the host's
temp area and answers with a token, and the program reads the file the token
names through the tab's ``UploadView``. The temp file is a cache: before a
pull, a slice comes from the browser and is dropped once read; after a pull,
every read comes from the landed file. ``pull()`` and ``discard()`` change
where a read comes from, never what it returns. The app never sees a path.

- ``UploadFileRef``: one file, NULL while empty.
- ``UploadFilesRef``: several, ``[]`` while empty, entry ``i`` as ``file(i)``.
- ``UploadedFileRef``: one entry of an ``UploadFilesRef``, the same reads.
- the commands ``Pull``, ``Slice``, ``Cancel``, ``Discard``, ``RemoveFile``,
  one wire op each, and the reads ``GetSlice``, ``GetBytes``, ``OpenFile``.
- ``UploadError`` and its subclasses, one per failure code the tab answers.

The tab holds all per file state (handle, token, running transfer). The
program holds none: every read asks, and waits for the one notify that
carries its request id.
"""

from __future__ import annotations

import asyncio
import contextvars
import logging
import uuid
from typing import TYPE_CHECKING, Any, ClassVar, NoReturn

from typing_extensions import Self

from nu.engine.structure import Declared
from nu.forms import Dict
from nu.lang import ScalarQuery, StreamQuery
from nu.lang.null import is_null
from nustd.ui.core import EVENT, Changed, Frame, Send, Session, Write, check_key
from nustd.ui.core.protocol import _op_of
from nustd.ui.core.uploads import UploadView

from .base import LeafRef
from .input import InputLeaf, _common, _Nullable


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable
    from pathlib import Path

    from nu.lang import Nu
    from nu.lang.args import IntArg, StrArg
    from nu.lang.runtime import Runtime
    from nustd.ui.core import Ref

    from ..vocab import ControlSize


__all__ = [
    "GET_BYTES_WARN",
    "STEP",
    "Cancel",
    "Discard",
    "FileGone",
    "GetBytes",
    "GetSlice",
    "NoFile",
    "OpenFile",
    "Pull",
    "RemoveFile",
    "Slice",
    "UploadCanceled",
    "UploadError",
    "UploadFailed",
    "UploadFileRef",
    "UploadFilesRef",
    "UploadRefused",
    "UploadTooLarge",
    "UploadedFileRef",
]

_log = logging.getLogger(__name__)


#: Bytes per piece ``open()`` yields unless told otherwise.
STEP = 1 << 20
#: ``get_bytes()`` logs a warning past this many bytes.
GET_BYTES_WARN = 16 << 20

#: The events the tab sends on an upload ref, besides ``change``.
PROGRESS = "progress"
UPLOAD = "upload"
SLICE = "slice"
DISCARD = "discard"


# --- errors ------------------------------------------------------------------


class UploadError(Exception):
    """A read or a pull on an upload ref that could not be served.

    The base of every upload failure, so an app catches one thing. ``code``
    is what the tab answered (``no_file``, ``unreadable``, ``canceled``,
    ``too_large``, ``refused``, ``network``).
    """

    code: ClassVar[str] = ""


class NoFile(UploadError):  # noqa: N818 - a state, not an error kind
    """Nothing is picked: the input is empty, or the entry is not there."""

    code = "no_file"


class FileGone(UploadError):  # noqa: N818 - a state, not an error kind
    """The file changed or moved on disk after the pick, so the tab cannot read it.

    The input keeps the file with ``state: "failed"`` and ``error:
    "unreadable"`` and asks the person to pick it again.
    """

    code = "unreadable"


class UploadCanceled(UploadError):  # noqa: N818 - a state, not an error kind
    """The transfer was canceled, by ``cancel()`` or by the person."""

    code = "canceled"


class UploadTooLarge(UploadError):  # noqa: N818 - a state, not an error kind
    """The bytes are over the intake's cap, so the server refused them (413)."""

    code = "too_large"


class UploadRefused(UploadError):  # noqa: N818 - a state, not an error kind
    """The server refused the transfer, or a token names nothing on the server.

    A tab that is not live, a token that was dropped or swept, or one that
    does not resolve inside the tab's own dir.
    """

    code = "refused"


class UploadFailed(UploadError):  # noqa: N818 - a state, not an error kind
    """The transfer broke on the way: a network drop mid POST."""

    code = "network"


_ERRORS: dict[str, type[UploadError]] = {
    cls.code: cls
    for cls in (NoFile, FileGone, UploadCanceled, UploadTooLarge, UploadRefused, UploadFailed)
}

_MESSAGES = {
    "no_file": "no file is picked",
    "unreadable": "the file changed or moved on disk after it was picked; pick it again",
    "canceled": "the transfer was canceled",
    "too_large": "the file is over the server's upload cap",
    "refused": "the server refused the transfer",
    "network": "the transfer broke on the way",
}


def _error(code: str, where: str) -> UploadError:
    """The error for ``code``, its message naming the ref at ``where``."""
    cls = _ERRORS.get(code, UploadFailed)
    reason = _MESSAGES.get(code, f"the transfer failed ({code})")
    return cls(f"{where}: {reason}")


def _check_answer(answer: dict[str, Any], where: str) -> str:
    """The token an answer names, or the error it reports, raised."""
    code = answer.get("error") or ""
    if not code and answer.get("state") == "canceled":
        code = "canceled"
    if code:
        raise _error(str(code), where)
    token = answer.get("token")
    if not isinstance(token, str) or not token:
        raise UploadRefused(f"{where}: the tab answered with no file")
    return token


# --- the tab's view, and the wait for one answer -----------------------------


def _view(rt: Runtime) -> UploadView:
    """This tab's ``UploadView``, or a ``LookupError`` saying who binds it."""
    if not rt.ctx.fabrics.has(UploadView):
        msg = (
            "upload refs need the tab's UploadView on the Context; nudle.serve binds it,"
            " a host of its own binds UploadView(root, sid) beside the Session"
        )
        raise LookupError(msg)
    return rt.ctx.fabrics.get(UploadView)


def _resolve(view: UploadView, token: str, where: str) -> Path:
    """The file ``token`` names, or ``UploadRefused`` when it names nothing."""
    try:
        return view.path(token)
    except (ValueError, FileNotFoundError) as exc:
        raise UploadRefused(f"{where}: {exc}") from None


async def _ask(
    session: Session,
    chain: tuple[tuple[str, str | None, dict], ...],
    op: str,
    payload: dict[str, Any],
    event: str,
) -> dict[str, Any]:
    """Send one command and wait for the notify that answers it.

    Subscribes on the node's path before the send, so an answer cannot land
    in between; takes the first notify whose ``event`` and ``rid`` match;
    unsubscribes however the wait ends. Only ``send`` and ``subscribe``, so
    any Session carries it (a nuspace worker's pipe too).

    Raises:
        ConnectionError: the session refused the subscribe or the send: the
            tab is gone.
    """
    path = tuple(seg for seg, _, _ in chain)
    rid = payload["rid"]
    loop = asyncio.get_running_loop()
    answered: asyncio.Future[dict[str, Any]] = loop.create_future()

    def hear(note: object) -> None:
        # Never raises: a session drops a callback that does.
        if (
            isinstance(note, dict)
            and note.get(EVENT) == event
            and note.get("rid") == rid
            and not answered.done()
        ):
            answered.set_result(note)

    try:
        sub = session.subscribe(path)
    except ConnectionError:
        raise
    except Exception as exc:
        raise ConnectionError(f"ui session closed: {exc}") from exc
    sub.bind(hear)
    try:
        try:
            await session.send(Frame(op, ref=path, payload=payload, chain=chain))
        except ConnectionError:
            raise
        except Exception as exc:
            raise ConnectionError(f"ui session closed: {exc}") from exc
        return await answered
    finally:
        sub.unbind(hear)
        sub.close()


async def _adrop(view: UploadView, token: object) -> None:
    """Delete the file ``token`` names, off the loop. No token, or not one of ours: nothing."""
    if not isinstance(token, str) or not token:
        return
    try:
        await asyncio.to_thread(view.drop, token)
    except ValueError:
        pass  # not a token: it names nothing of ours


def _int(name: str, value: object, *, optional: bool = False) -> int | None:
    """``value`` as a range bound: an int, or None when ``optional``."""
    if optional and (value is None or is_null(value)):
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{name} is an int, not {value!r}"
        raise TypeError(msg)
    return value


def _read_range(path: Path, start: int, end: int | None) -> bytes:
    """``[start:end]`` of the file, python slice semantics, clamped to its size."""
    with path.open("rb") as file:
        size = file.seek(0, 2)
        lo, hi, _ = slice(start, end).indices(size)
        if hi <= lo:
            return b""
        file.seek(lo)
        return file.read(hi - lo)


def _pieces(path: Path, start: int, end: int | None, step: int) -> Any:
    """The bytes of ``[start:end]``, ``step`` at a time, from one open file."""
    with path.open("rb") as file:
        size = file.seek(0, 2)
        pos, stop, _ = slice(start, end).indices(size)
        file.seek(pos)
        while pos < stop:
            piece = file.read(min(step, stop - pos))
            if not piece:
                return
            yield piece
            pos += len(piece)


# --- commands ----------------------------------------------------------------


class _UploadCommand(Send):
    """A command to one upload node, its op the class name. Abstract.

    The payload is ``key`` (which file, null for the whole input), then a
    fresh ``rid`` and the tab's intake ``url`` where the command needs them,
    then the arguments named in ``_payload_fields``. A command with an
    ``_answer`` event waits for the notify that carries its rid.
    """

    #: Mint a request id per run.
    _rid: ClassVar[bool] = False
    #: Name the tab's intake url.
    _url: ClassVar[bool] = False
    #: The notify event that answers it; None sends and returns at once.
    _answer: ClassVar[str | None] = None

    @classmethod
    def op(cls) -> str:
        """The wire op this command ships as: its class name in snake case."""
        return _op_of(object.__new__(cls))

    @classmethod
    def _payload(cls, key: object, view: UploadView | None, values: list[object]) -> dict:
        payload: dict[str, Any] = {"key": key}
        if cls._rid:
            payload["rid"] = uuid.uuid4().hex
        if cls._url and view is not None:
            payload["url"] = view.url
        payload.update(zip(cls._payload_fields, values, strict=True))
        return payload

    @classmethod
    async def _aexchange(
        cls,
        rt: Runtime,
        ref: Ref,
        ref_nid: int,
        values: list[object],
        answer: str | None = None,
    ) -> tuple[dict[str, Any], UploadView, str]:
        """Send this command on ``ref`` and wait: the answer, the view, the ref's name.

        ``answer`` overrides the event waited for, so ``open`` waits on a
        ``pull`` for its ``upload`` notify.
        """
        event = answer or cls._answer or ""
        session = rt.ctx.fabrics.get(Session)
        view = _view(rt)
        chain, key = await ref._aupload_target(rt, ref_nid)  # type: ignore[attr-defined]
        payload = cls._payload(key, view, values)
        note = await _ask(session, chain, cls.op(), payload, event)
        return note, view, _where(chain, key)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunks = children[1:]
        cls = type(self)

        async def athunk(rt: Runtime) -> None:
            ref_nid = rt.program.children[nid][0]
            values = [await t(rt) for t in value_thunks]
            if cls._answer is not None:
                answer, view, _ = await cls._aexchange(rt, ref, ref_nid, values)
                await self._aanswered(answer, view)
                return
            session = rt.ctx.fabrics.get(Session)
            view = _view(rt) if cls._url else None
            chain, key = await ref._aupload_target(rt, ref_nid)  # type: ignore[attr-defined]
            path = tuple(seg for seg, _, _ in chain)
            payload = cls._payload(key, view, values)
            await session.send(Frame(cls.op(), ref=path, payload=payload, chain=chain))

        return athunk

    async def _aanswered(self, answer: dict[str, Any], view: UploadView) -> None:
        """What the program does with the answer. Nothing, unless a command says."""


class Pull(_UploadCommand):
    """Start the whole file toward the server's cache; returns at once.

    Payload ``{key, rid, url}``. A pull for a file that is landed or on its
    way does nothing new: the tab answers with the token it has. After a
    ``discard`` or a failure it starts over. Its end is an ``upload`` notify.
    """

    _rid = True
    _url = True


class Slice(_UploadCommand):
    """Ask the tab for ``[start:end]`` of a file and wait for where it put it.

    Payload ``{key, rid, url, start, end}``, ``end`` null for the end of the
    file. Answered by a ``slice`` notify. Run on its own it drops a fresh
    slice file at once; ``get_slice`` is what reads one.
    """

    _rid = True
    _url = True
    _answer = SLICE
    _payload_fields = ("start", "end")

    async def _aanswered(self, answer: dict[str, Any], view: UploadView) -> None:
        if not answer.get("error") and not answer.get("cached"):
            await _adrop(view, answer.get("token"))


class Cancel(_UploadCommand):
    """Abort a running pull; a read waiting on it raises ``UploadCanceled``.

    Payload ``{key}``, key null on ``UploadFilesRef`` for every running pull.
    """


class Discard(_UploadCommand):
    """Drop the file's cache on the server. The selection stays.

    Payload ``{key, rid}``. The tab forgets the token and answers with a
    ``discard`` notify naming it (null when nothing was landed); the program
    deletes that file. The next read that needs the file pulls it again.
    """

    _rid = True
    _answer = DISCARD

    async def _aanswered(self, answer: dict[str, Any], view: UploadView) -> None:
        await _adrop(view, answer.get("token"))


class RemoveFile(_UploadCommand):
    """Take one entry out of an ``UploadFilesRef``'s selection.

    Payload ``{key}``, the entry's index. The tab drops the handle and its
    cache and sends a ``change``.
    """


# --- reads -------------------------------------------------------------------


class GetSlice(ScalarQuery):
    """The bytes of ``[start:end]`` of a picked file, in memory.

    Args:
        ref: an ``UploadFileRef`` or an ``UploadedFileRef``.
        start: the first byte; negative counts from the end.
        end: one past the last byte, None for the end of the file; negative
            counts from the end.

    Notes:
        - Python slice semantics, clamped: a range past the end is cut, an
          inverted one is empty.
        - Landed, the bytes come from the cache and the cache stays. Not
          landed, the tab POSTs just the range; the slice file is read whole
          and deleted at once.
        - Raises the ``UploadError`` the tab answers with (``NoFile`` on an
          empty input), ``ConnectionError`` when the tab is gone.

    Yields:
        ``bytes``.

    Example:
        nu.let(csv.get_slice(0, 4096), lambda head: show_columns(head))
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, start: IntArg = 0, end: IntArg | None = None) -> None:
        super().__init__(ref, start, end)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> bytes:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        bounds = children[1:]

        async def athunk(rt: Runtime) -> bytes:
            ref_nid = rt.program.children[nid][0]
            start, end = [await t(rt) for t in bounds] if bounds else (0, None)
            start = _int("get_slice start", start) or 0
            end = _int("get_slice end", end, optional=True)
            return await self._aread(rt, ref, ref_nid, start, end)

        return athunk

    async def _aread(
        self, rt: Runtime, ref: Ref, ref_nid: int, start: int, end: int | None
    ) -> bytes:
        answer, view, where = await Slice._aexchange(rt, ref, ref_nid, [start, end])
        token = _check_answer(answer, where)
        self._before_read(where, answer)
        if answer.get("cached"):
            return await asyncio.to_thread(_read_range, _resolve(view, token, where), start, end)
        try:
            path = _resolve(view, token, where)
            return await asyncio.to_thread(path.read_bytes)
        finally:
            await _adrop(view, token)

    def _before_read(self, where: str, answer: dict[str, Any]) -> None:
        """A hook before the bytes are read; ``GetBytes`` warns there."""


class GetBytes(GetSlice):
    """The whole of a picked file, in memory.

    Args:
        ref: an ``UploadFileRef`` or an ``UploadedFileRef``.

    Notes:
        - Logs a warning past 16 MiB naming the ref and the size: ``open()``
          reads a big file in pieces. There is no cap of its own; the
          intake's cap still holds.
        - Same sources and errors as ``get_slice``.

    Yields:
        ``bytes``.

    Example:
        nu.let(cfg.get_bytes(), lambda raw: load(raw))
    """

    def __init__(self, ref: Ref) -> None:
        ScalarQuery.__init__(self, ref)

    def _before_read(self, where: str, answer: dict[str, Any]) -> None:
        size = answer.get("size")
        if isinstance(size, int) and size > GET_BYTES_WARN:
            _log.warning(
                "nustd.ui %s: get_bytes() reads %d bytes into memory; open() reads a big file"
                " in pieces",
                where,
                size,
            )


class OpenFile(StreamQuery):
    """The bytes of ``[start:end]`` of a picked file, a piece at a time (lazy).

    Args:
        ref: an ``UploadFileRef`` or an ``UploadedFileRef``.
        start: the first byte; negative counts from the end.
        end: one past the last byte, None for the end of the file.
        step: bytes per piece; the last piece may be shorter.

    Notes:
        - The first pull waits for the file to land, pulling it if it is not
          (a landed file answers at once), then reads the cache one piece per
          pull, each off the event loop. Nothing runs ahead of the pull.
        - The cache stays after the stream ends; ``discard()`` drops it.
        - Raises the ``UploadError`` the pull ended with (``UploadCanceled``
          on ``cancel()``) at the first pull.

    Yields:
        A stream of ``bytes`` pieces, in order, that join to the range.

    Example:
        nu.ReactEvery(csv.on_upload(), BuildIndex(csv.open(step=1 << 20)))
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self, ref: Ref, start: IntArg = 0, end: IntArg | None = None, step: IntArg = STEP
    ) -> None:
        super().__init__(ref, start, end, step)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        _, start_t, end_t, step_t = children

        async def athunk(rt: Runtime) -> AsyncIterator[bytes]:
            ref_nid = rt.program.children[nid][0]
            start = _int("open start", await start_t(rt)) or 0
            end = _int("open end", await end_t(rt), optional=True)
            step = _int("open step", await step_t(rt)) or 0
            if step <= 0:
                msg = f"open step must be positive, got {step}"
                raise ValueError(msg)
            return _astream(rt, ref, ref_nid, start, end, step)

        return athunk


async def _astream(
    rt: Runtime, ref: Ref, ref_nid: int, start: int, end: int | None, step: int
) -> AsyncIterator[bytes]:
    """Wait for the file to land, then read the cache ``step`` at a time."""
    answer, view, where = await Pull._aexchange(rt, ref, ref_nid, [], answer=UPLOAD)
    token = _check_answer(answer, where)
    pieces = _pieces(_resolve(view, token, where), start, end, step)
    try:
        while True:
            try:
                piece = await asyncio.to_thread(next, pieces, None)
            except FileNotFoundError:
                raise UploadRefused(f"{where}: the cached file is gone") from None
            if piece is None:
                return
            yield piece
    finally:
        try:
            pieces.close()
        except ValueError:
            # Cancelled mid pull: the thread still runs the generator, so it
            # cannot be closed here; it closes when collected.
            pass


def _where(chain: tuple[tuple[str, str | None, dict], ...], key: object) -> str:
    """The ref's address for messages: ``page/form/file``, plus ``.file(i)`` for an entry."""
    where = "/".join(seg for seg, _, _ in chain)
    return where if key is None else f"{where}.file({key})"


# --- refs --------------------------------------------------------------------


def _limit(name: str, value: object) -> int | None:
    """A size or count limit: a positive int, or None for none."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        msg = f"{name} is a positive int or None, not {value!r}"
        raise ValueError(msg)
    return value


class _FileReads:
    """Mixin: the reads of one file, on ``UploadFileRef`` and ``UploadedFileRef``.

    Each is an interaction over the ws; the bytes come over http into the
    server's cache and are read there, so a read never holds the ws.
    """

    def get_slice(self, start: IntArg = 0, end: IntArg | None = None) -> GetSlice:
        """The bytes of ``[start:end]``, python slice semantics, clamped. See ``GetSlice``."""
        return GetSlice(self, start, end)  # type: ignore[arg-type]

    def get_bytes(self) -> GetBytes:
        """The whole file in memory; warns past 16 MiB. See ``GetBytes``."""
        return GetBytes(self)  # type: ignore[arg-type]

    def open(self, start: IntArg = 0, end: IntArg | None = None, step: IntArg = STEP) -> OpenFile:
        """A lazy stream of ``bytes`` pieces of ``[start:end]``, pulling first. See ``OpenFile``."""
        return OpenFile(self, start, end, step)  # type: ignore[arg-type]

    def pull(self) -> Nu:
        """Start the whole file toward the server's cache; returns at once. See ``Pull``."""
        return Pull(self)  # type: ignore[arg-type]

    def cancel(self) -> Nu:
        """Abort a running pull; a read waiting on it raises ``UploadCanceled``."""
        return Cancel(self)  # type: ignore[arg-type]

    def discard(self) -> Nu:
        """Drop the server's cache of the file; the selection stays. See ``Discard``."""
        return Discard(self)  # type: ignore[arg-type]


class _UploadInput(InputLeaf):
    """What both upload inputs are: a picker and a drop zone. Abstract.

    The value is the selection, never bytes. A program cannot put a file in
    a picker (browsers forbid it), so ``set`` raises when the tree is built
    and the slot takes no ``value=``; ``reset()`` clears the selection.
    ``on_change`` hears the selection only (pick, drop, paste, remove,
    reset); ``on_progress`` and ``on_upload`` hear the pulls.
    """

    def set(self, *_: object, **__: object) -> NoReturn:
        msg = (
            f"{type(self).__name__}.set: a program cannot put a file in a picker; reset() clears it"
        )
        raise TypeError(msg)

    async def _aupload_target(
        self, rt: Runtime, nid: int
    ) -> tuple[tuple[tuple[str, str | None, dict], ...], object]:
        """The chain a command ships on, and the ``key`` it names: the whole input."""
        return await self._aresolve_chain(rt, nid), None

    def on_progress(self) -> Changed:
        """A pull moving: ``{event: "progress", key, rid, sent, size}``.

        Throttled in the browser to at most every 100 ms, and only when it
        moved by 1%. Drawing it, or not, is the app's call.
        """
        return Changed(self, PROGRESS)

    def on_upload(self) -> Changed:
        """A pull ended: ``{event: "upload", key, rid, token, state, size, error}``.

        ``state`` is ``landed``, ``failed`` or ``canceled``; ``error`` the
        code of a failure, "" when landed. Pulls only, never slices.
        """
        return Changed(self, UPLOAD)

    def set_accept(self, accept: StrArg) -> Nu:
        """Which files the picker offers and a drop takes: ``.csv``, ``image/*``, ..."""
        return Write(self, Dict.of(accept=accept))

    def set_prompt(self, text: StrArg) -> Nu:
        """The text in the drop zone."""
        return Write(self, Dict.of(prompt=text))

    def set_max_size(self, size: IntArg | None) -> Nu:
        """The largest file a pick takes, in bytes; None for no limit."""
        return Write(self, Dict.of(max_size=size))


class UploadFileRef(_Nullable, _FileReads, _UploadInput):
    """One file the person hands over: picked, dropped or pasted.

    The value is ``{key, name, mime, size, modified, state, sent, error}``,
    NULL while empty (None in a Form). Picking moves no bytes: the program
    reads what it wants with ``get_slice``, ``get_bytes`` or ``open``, and
    ``pull()`` fetches the whole file ahead of the reads.

    Args:
        accept: which files the picker offers and a drop takes, as the
            browser's ``accept`` (``.csv``, ``image/*``, a list joined by
            commas). "" takes any.
        max_size: the largest file a pick takes, in bytes. Over it the pick
            is refused in the browser with a message and never becomes the
            value. None for no limit (the intake's cap still holds).
        prompt: the text in the drop zone.

    Notes:
        - ``key`` is minted by the browser and names the handle on the wire.
          ``name`` and ``mime`` are the client's claims, not facts: sniff
          with ``get_slice`` before trusting them.
        - ``state`` is ``picked``, ``pulling``, ``landed`` or ``failed``;
          ``sent`` the bytes sent of the last pull; ``error`` the code of the
          last failure.
        - Every read on an empty input raises ``NoFile``.

    Example:
        csv = UploadFileRef.slot(accept=".csv", label="Orders")
        nu.ReactEvery(csv.on_change(),
            nu.let(csv.get_slice(0, 4096), show_columns) >> csv.pull())
    """

    _wire_type = "UploadFileRef"

    @classmethod
    def slot(
        cls,
        *,
        accept: str = "",
        max_size: int | None = None,
        prompt: str = "",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            accept=accept,
            max_size=_limit("UploadFileRef max_size", max_size),
            prompt=prompt,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )


# Set while ``file(i)`` builds its entry, the one child an UploadFilesRef admits.
_building_entry: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_building_entry", default=False
)


class UploadFilesRef(_UploadInput):
    """Several files the person hands over; a second pick or drop appends.

    The value is a list of the same dicts ``UploadFileRef`` holds, ``[]``
    while empty. Entry ``i`` is ``file(i)``, with every read of one file.
    ``pull()`` and ``cancel()`` act on every file at once; ``on_progress``
    and ``on_upload`` fire per file, the ``key`` in the payload saying which.

    Args:
        accept: which files the picker offers and a drop takes.
        max_size: the largest file a pick takes, in bytes; None for none.
        max_files: the most files the selection holds; a pick past it is cut
            with a message. None for no limit.
        prompt: the text in the drop zone.

    Notes:
        - ``file(i)`` names its entry by position; the browser resolves it
          to the entry's key when the command lands, and answers by key. A
          read waits on its own request id, so a remove in between cannot
          hand it another file's bytes.
        - Each row in the browser has a remove button; ``remove(i)`` is the
          program's.

    Example:
        photos = UploadFilesRef.slot(accept="image/*", max_files=20)
        nu.ReactEvery(photos.on_change(), photos.pull())
        nu.let(photos.file(0).get_slice(0, 16), sniff)
    """

    _wire_type = "UploadFilesRef"

    @classmethod
    def slot(
        cls,
        *,
        accept: str = "",
        max_size: int | None = None,
        max_files: int | None = None,
        prompt: str = "",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            accept=accept,
            max_size=_limit("UploadFilesRef max_size", max_size),
            max_files=_limit("UploadFilesRef max_files", max_files),
            prompt=prompt,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def _lift(self, raw: object) -> object:
        return [] if raw is None or is_null(raw) else raw

    def _admit(self, address: object) -> None:
        if _building_entry.get():
            return
        msg = (
            f"UploadFilesRef holds no children; reach entry {address!r} of the selection"
            f" with .file({address!r})"
        )
        raise TypeError(msg)

    def file(self, i: IntArg) -> UploadedFileRef:
        """Entry ``i`` of the selection, with every read of one file.

        Args:
            i: the entry's position, an int >= 0 or an int term.

        Notes:
            - Resolved to the entry's key in the browser when each command
              lands. An index past the selection raises ``NoFile``.
        """
        check_key("UploadFilesRef", i, names=False)
        reset = _building_entry.set(True)
        try:
            return UploadedFileRef(i, parent_ref=self)
        finally:
            _building_entry.reset(reset)

    def pull(self) -> Nu:
        """Start every file in the selection toward the server's cache; returns at once."""
        return Pull(self)

    def cancel(self) -> Nu:
        """Abort every running pull."""
        return Cancel(self)

    def remove(self, i: IntArg) -> Nu:
        """Take entry ``i`` out of the selection (a program can remove, not add)."""
        return RemoveFile(self.file(i))

    def set_max_files(self, count: IntArg | None) -> Nu:
        """The most files the selection holds; None for no limit."""
        return Write(self, Dict.of(max_files=count))


class UploadedFileRef(_FileReads, LeafRef):
    """Entry ``i`` of an ``UploadFilesRef``: the reads of one file.

    A leaf, so an ``ItemRef`` with nothing under it. Built by
    ``files.file(i)``, never declared. Its commands ship on the
    files node itself, ``key`` set to the index, and the browser resolves
    the index to the entry's key when the command lands.

    Example:
        nu.let(photos.file(0).get_bytes(), lambda raw: thumbnail(raw))
    """

    _wire_type: ClassVar[str] = "UploadedFileRef"

    async def _aupload_target(
        self, rt: Runtime, nid: int
    ) -> tuple[tuple[tuple[str, str | None, dict], ...], object]:
        """The files node's chain, and the entry's index as the ``key``."""
        chain = await self._aresolve_chain(rt, nid)
        *files, (segment, _, _) = chain
        if not segment.isdigit():
            msg = f"UploadFilesRef.file takes a position >= 0, not {segment!r}"
            raise IndexError(msg)
        return tuple(files), int(segment)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            msg = (
                "UploadFilesRef.file(i) is read with get_slice, get_bytes or open;"
                " read the UploadFilesRef itself for the selection"
            )
            raise TypeError(msg)

        return athunk
