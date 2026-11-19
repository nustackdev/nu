"""The fs interactions: read, look, list and stream files under a mount.

Slot 0 of every atom is the mount: an ``FsRef`` yielding the ``FsFabric``
bound under its tag. Everything else is a child, so a path, a range or a
pattern can come from any term, such as a name another op yielded.

===========  ====================================  ===========  =======
atom         slots                                 sort         mutates
===========  ====================================  ===========  =======
FsReadText   (ref, p, encoding[, default])         ScalarQuery  -
FsReadBytes  (ref, p, start, end[, default])       ScalarQuery  -
FsStat       (ref, p)                              ScalarQuery  -
FsHas        (ref, p, kind)                        ScalarQuery  -
FsUsage      (ref,)                                ScalarQuery  -
FsWhere      (ref, p)                              ScalarQuery  -
FsDigest     (ref, p, algo)                        ScalarQuery  -
FsList       (ref, p, pattern, recursive, kind)    StreamQuery  -
FsOpen       (ref, p, start, end, step)            StreamQuery  -
FsLines      (ref, p, encoding)                    StreamQuery  -
===========  ====================================  ===========  =======

Paths are relative to the mount, a ``str``, a ``PurePath`` or a term
yielding one (a ``nustd.pathlib.Path``); see ``FsFabric`` for the checks.

A sync run calls the fabric in place. An async run calls it in a thread, and
a stream reads each piece in a thread, so no file call blocks the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

from nu.lang import Nu, ScalarQuery, StreamQuery
from nu.lang.null import is_null
from nu.lang.sentinels import UNSET

from .fabric import STEP, FsFabric


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang.runtime import Runtime


__all__ = [
    "FsDigest",
    "FsHas",
    "FsLines",
    "FsList",
    "FsOpen",
    "FsReadBytes",
    "FsReadText",
    "FsStat",
    "FsUsage",
    "FsWhere",
]


# --- child helpers ----------------------------------------------------------


def ref_node(ref: object) -> Nu:
    """The mount slot, a term such as an ``FsRef``; anything else is refused."""
    if not isinstance(ref, Nu):
        msg = (
            f"the mount slot is a term, such as an FsRef, got {ref!r}: "
            "build fs terms from the ref, as ref.read_text(path)"
        )
        raise TypeError(msg)
    return ref


def fabric_of(value: object) -> FsFabric:
    """The open mount behind the slot's value; NULL means nothing was bound."""
    if is_null(value) or value is None:
        tag = value.hint if is_null(value) else ""
        if tag:
            msg = f"no fs mount {tag!r} bound; wrap with fs.mount(..., tag={tag!r})"
        else:
            msg = "no fs mount bound; wrap with fs.mount(path, body=...)"
        raise RuntimeError(msg)
    if not isinstance(value, FsFabric):
        raise TypeError(f"the mount slot yielded {type(value).__name__}, not an FsFabric")
    return value


def optional(value: object) -> object:
    """A child that may be left out: NULL reads as None."""
    return None if is_null(value) else value


async def athread(make: Callable[..., Iterator], *args: object) -> AsyncIterator:
    """The stream ``make(*args)`` builds, built and pulled a piece at a time in a thread."""
    pieces = await asyncio.to_thread(make, *args)
    try:
        while True:
            piece = await asyncio.to_thread(next, pieces, UNSET)
            if piece is UNSET:
                return
            yield piece
    finally:
        # Cancelled mid-pull, the thread may still run the generator, so it
        # cannot be closed here; it closes when collected.
        with contextlib.suppress(ValueError):
            pieces.close()  # type: ignore[attr-defined]


# --- whole reads ------------------------------------------------------------


class FsReadText(ScalarQuery):
    """The text of a file, whole.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        encoding: the text encoding.
        default: what a missing file yields. Left out, a missing file raises
            ``FileNotFoundError``.

    Notes:
        - The whole value sits in memory: stream a big file with ``FsLines``
          or ``FsOpen``.
        - Only a missing file takes the default. A dir, an escape or a bad
          encoding still raises.

    Yields:
        A ``str``.

    Example:
        data.read_text("notes.md", default="")
    """

    def __init__(
        self, ref: object, p: object, encoding: object = "utf-8", default: object = UNSET
    ) -> None:
        if default is UNSET:
            super().__init__(ref_node(ref), p, encoding)
        else:
            super().__init__(ref_node(ref), p, encoding, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, encoding, *rest = children
        default = rest[0] if rest else None

        def thunk(rt: Runtime) -> object:
            fabric = fabric_of(ref(rt))
            try:
                return fabric.read_text(p(rt), encoding(rt))
            except FileNotFoundError:
                if default is None:
                    raise
                return default(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, encoding, *rest = children
        default = rest[0] if rest else None

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            path, enc = await p(rt), await encoding(rt)
            try:
                return await asyncio.to_thread(fabric.read_text, path, enc)
            except FileNotFoundError:
                if default is None:
                    raise
                return await default(rt)

        return athunk


class FsReadBytes(ScalarQuery):
    """The bytes of a range of a file, whole.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        start: the first byte, from 0.
        end: one past the last byte; None for the end of the file. The range
            clamps to the file's size, so one past the end reads short.
        default: what a missing file yields. Left out, a missing file raises
            ``FileNotFoundError``.

    Notes:
        - A negative bound is a ``ValueError``.
        - The whole range sits in memory: stream a big one with ``FsOpen``.

    Yields:
        ``bytes``.

    Example:
        data.read_bytes("cat.png", 0, 8)
    """

    def __init__(
        self,
        ref: object,
        p: object,
        start: object = 0,
        end: object = None,
        default: object = UNSET,
    ) -> None:
        if default is UNSET:
            super().__init__(ref_node(ref), p, start, end)
        else:
            super().__init__(ref_node(ref), p, start, end, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, start, end, *rest = children
        default = rest[0] if rest else None

        def thunk(rt: Runtime) -> object:
            fabric = fabric_of(ref(rt))
            try:
                return fabric.read_bytes(p(rt), start(rt), optional(end(rt)))  # type: ignore[arg-type]
            except FileNotFoundError:
                if default is None:
                    raise
                return default(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, start, end, *rest = children
        default = rest[0] if rest else None

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            args = (await p(rt), await start(rt), optional(await end(rt)))
            try:
                return await asyncio.to_thread(fabric.read_bytes, *args)  # type: ignore[arg-type]
            except FileNotFoundError:
                if default is None:
                    raise
                return await default(rt)

        return athunk


# --- looks ------------------------------------------------------------------


class FsStat(ScalarQuery):
    """What sits at a path: its entry, or None when nothing does.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the path in the mount.

    Notes:
        - A link is reported as the link (``kind="link"``), never followed,
          so its target may lie outside the mount.
        - Missing yields None rather than NULL: NULL is a context read's
          answer, and a stat is a look at the disk.

    Yields:
        A dict ``{path, name, kind, size, mtime, mode}``: ``path`` a
        ``PurePosixPath`` relative to the mount, ``kind`` one of ``"file"``,
        ``"dir"``, ``"link"``, ``"other"``, ``mode`` the permission bits. None
        when nothing is there.

    Example:
        data.stat("notes.md")
    """

    def __init__(self, ref: object, p: object) -> None:
        super().__init__(ref_node(ref), p)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        def thunk(rt: Runtime) -> object:
            return fabric_of(ref(rt)).stat(p(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.stat, await p(rt))

        return athunk


class FsHas(ScalarQuery):
    """Whether something sits at a path.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the path in the mount.
        kind: None for anything, ``"file"`` or ``"dir"`` for that kind only.

    Notes:
        - A link is followed: a dangling one is not there.

    Yields:
        A ``bool``.

    Example:
        data.has("cache", kind="dir")
    """

    def __init__(self, ref: object, p: object, kind: object = None) -> None:
        super().__init__(ref_node(ref), p, kind)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, kind = children

        def thunk(rt: Runtime) -> bool:
            return fabric_of(ref(rt)).has(p(rt), optional(kind(rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, kind = children

        async def athunk(rt: Runtime) -> bool:
            fabric = fabric_of(await ref(rt))
            args = (await p(rt), optional(await kind(rt)))
            return await asyncio.to_thread(fabric.has, *args)  # type: ignore[arg-type]

        return athunk


class FsUsage(ScalarQuery):
    """How full the mount's file system is.

    Args:
        ref: the mount slot, an ``FsRef``.

    Notes:
        - The numbers are the whole file system the mount sits on, not the
          mount's own files.

    Yields:
        A dict ``{total, free, used}`` in bytes.

    Example:
        data.usage()
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref_node(ref))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        def thunk(rt: Runtime) -> object:
            return fabric_of(ref(rt)).usage()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.usage)

        return athunk


class FsWhere(ScalarQuery):
    """The absolute path of a path in the mount, for code outside Nu.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the path in the mount; ``"."`` for the mount itself.

    Notes:
        - Checked like any other path, so it never names a place outside the
          mount. Nothing needs to sit there.
        - What to hand a tool or an agent as its working dir.

    Yields:
        An absolute ``str`` path.

    Example:
        data.where("work")
    """

    def __init__(self, ref: object, p: object = ".") -> None:
        super().__init__(ref_node(ref), p)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        def thunk(rt: Runtime) -> str:
            return fabric_of(ref(rt)).where(p(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        async def athunk(rt: Runtime) -> str:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.where, await p(rt))

        return athunk


class FsDigest(ScalarQuery):
    """The hex digest of a file's bytes, read a piece at a time.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        algo: a ``hashlib`` algorithm name.

    Notes:
        - The file is never held whole in memory.

    Yields:
        A hex ``str``.

    Example:
        data.digest("cat.png")
    """

    def __init__(self, ref: object, p: object, algo: object = "sha256") -> None:
        super().__init__(ref_node(ref), p, algo)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, algo = children

        def thunk(rt: Runtime) -> str:
            return fabric_of(ref(rt)).digest(p(rt), algo(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, algo = children

        async def athunk(rt: Runtime) -> str:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.digest, await p(rt), await algo(rt))

        return athunk


# --- streams ----------------------------------------------------------------


class FsList(StreamQuery):
    """The entries of a dir, a lazy stream.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the dir's path in the mount; ``"."`` for the mount itself.
        pattern: an ``fnmatch`` pattern each entry's name must match.
        recursive: walk the dirs below too. Links to dirs are listed, never
            walked.
        kind: None for every entry, else ``"file"``, ``"dir"``, ``"link"`` or
            ``"other"`` only.

    Notes:
        - Names come sorted within each dir, a dir's own entries before what
          lies below it. Sort them any other way with ``nu.SortBy``.
        - A missing dir raises ``FileNotFoundError``, a file
          ``NotADirectoryError``, when the stream starts.

    Yields:
        A stream of entry dicts, as ``FsStat`` gives them.

    Example:
        nu.Collect(data.list("logs", pattern="*.log", recursive=True))
    """

    def __init__(
        self,
        ref: object,
        p: object = ".",
        pattern: object = "*",
        recursive: object = False,
        kind: object = None,
    ) -> None:
        super().__init__(ref_node(ref), p, pattern, recursive, kind)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, pattern, recursive, kind = children

        def thunk(rt: Runtime) -> object:
            fabric = fabric_of(ref(rt))
            return fabric.listing(p(rt), pattern(rt), bool(recursive(rt)), optional(kind(rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, pattern, recursive, kind = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            args = (
                await p(rt),
                await pattern(rt),
                bool(await recursive(rt)),
                optional(await kind(rt)),
            )
            return athread(fabric.listing, *args)

        return athunk


class FsOpen(StreamQuery):
    """The bytes of a range of a file, a piece at a time (lazy).

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        start: the first byte, from 0.
        end: one past the last byte; None for the end of the file. The range
            clamps to the file's size.
        step: bytes per piece; the last piece may be shorter.

    Notes:
        - Each pull reads one piece, and nothing runs ahead of the pull. An
          async run reads each piece in a thread.
        - A missing file raises ``FileNotFoundError`` at the first pull.
        - The mount must stay bound while the stream is drained.

    Yields:
        A stream of ``bytes`` pieces, in order, that join to the range.

    Example:
        Media.put_stream(data.open("cat.png"))
    """

    def __init__(
        self,
        ref: object,
        p: object,
        start: object = 0,
        end: object = None,
        step: object = STEP,
    ) -> None:
        super().__init__(ref_node(ref), p, start, end, step)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, start, end, step = children

        def thunk(rt: Runtime) -> object:
            fabric = fabric_of(ref(rt))
            return fabric.pieces(p(rt), start(rt), optional(end(rt)), step(rt))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, start, end, step = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            args = (await p(rt), await start(rt), optional(await end(rt)), await step(rt))
            return athread(fabric.pieces, *args)

        return athunk


class FsLines(StreamQuery):
    r"""The lines of a text file, without their newline, a line at a time (lazy).

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        encoding: the text encoding.

    Notes:
        - ``\r\n`` reads as ``\n``, so no line keeps a ``\r``.
        - A last line with no newline is yielded as it is.
        - A missing file raises ``FileNotFoundError`` at the first pull.

    Yields:
        A stream of ``str`` lines.

    Example:
        nu.Collect(data.lines("app.log"))
    """

    def __init__(self, ref: object, p: object, encoding: object = "utf-8") -> None:
        super().__init__(ref_node(ref), p, encoding)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, encoding = children

        def thunk(rt: Runtime) -> object:
            return fabric_of(ref(rt)).lines(p(rt), encoding(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, encoding = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            return athread(fabric.lines, await p(rt), await encoding(rt))

        return athunk
