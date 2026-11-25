"""Upload inputs: a file the person hands over, read by the program on demand.

A picked file is a handle in the browser tab, never bytes on the server. The
program decides if, when and how much of it moves: a slice to sniff a header,
the whole file to keep, nothing at all for a name to show. So the value of an
upload input is the selection only (name, size, state), and every byte read
is an interaction on the ref.

- ``UploadFileRef``: one file, NULL while empty.
- ``UploadFilesRef``: several, ``[]`` while empty, entry ``i`` as ``file(i)``.
- ``UploadedFileRef``: one entry of an ``UploadFilesRef``, the same reads.

Only the refs live here. The commands and reads they hand out, the errors
those raise, the temp area and its intake are ``nustd.ui.uploads``.
"""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any, ClassVar, NoReturn

from typing_extensions import Self

from nu.forms import Dict, Iterator
from nu.lang.null import is_null
from nustd.ui.core import Changed, Write, check_key
from nustd.ui.uploads.interactions import (
    PROGRESS,
    STEP,
    UPLOAD,
    Cancel,
    Discard,
    GetBytes,
    GetSlice,
    OpenFile,
    Pull,
    RemoveFile,
)

from .base import LeafRef
from .input import InputLeaf, _common, _Nullable


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import IntArg, StrArg
    from nu.lang.runtime import Runtime

    from ..vocab import ControlSize


__all__ = ["UploadFileRef", "UploadFilesRef", "UploadedFileRef"]


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

    def open(self, start: IntArg = 0, end: IntArg | None = None, step: IntArg = STEP) -> Iterator:
        """A lazy stream of ``bytes`` pieces of ``[start:end]``, pulling first. See ``OpenFile``."""
        return Iterator(OpenFile(self, start, end, step))  # type: ignore[arg-type]

    def pull(self) -> Nu:
        """Start the whole file toward the server's cache; returns at once. See ``Pull``."""
        return Pull(self)  # type: ignore[arg-type]

    def cancel(self) -> Nu:
        """Abort a running pull; a read waiting on it raises ``UploadCanceled``."""
        return Cancel(self)  # type: ignore[arg-type]

    def discard(self) -> Nu:
        """Drop the server's cache of the file; the selection stays. See ``Discard``."""
        return Discard(self)  # type: ignore[arg-type]


class _FileInput(InputLeaf):
    """What every input holding a file handle is: upload or capture. Abstract.

    The value is the file's metadata, never bytes, and the bytes stay in the
    browser until a read asks. A program cannot put a file in (browsers
    forbid it), so ``set`` raises when the tree is built and the slot takes
    no ``value=``; ``reset()`` clears it. ``on_change`` hears the person's
    moves only; ``on_progress`` and ``on_upload`` hear the pulls.
    """

    def set(self, *_: object, **__: object) -> NoReturn:
        msg = (
            f"{type(self).__name__}.set: a program cannot put a file in a picker"
            " or a take in a recorder; reset() clears it"
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


class _UploadInput(_FileInput):
    """What both upload inputs are: a picker and a drop zone. Abstract.

    ``on_change`` hears the selection only (pick, drop, paste, remove,
    reset).
    """

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
