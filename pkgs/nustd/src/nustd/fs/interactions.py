"""The fs interactions: read, look, list, stream and write files under a mount.

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
FsHeld       (ref, p)                              ScalarQuery  -
FsList       (ref, p, pattern, recursive, kind)    StreamQuery  -
FsOpen       (ref, p, start, end, step)            StreamQuery  -
FsLines      (ref, p, encoding)                    StreamQuery  -
===========  ====================================  ===========  =======

===============  ====================================  ================  =======
atom             slots                                 sort              mutates
===============  ====================================  ================  =======
FsWriteText      (ref, p, text, exclusive, mode)       Command           {0}
FsWriteBytes     (ref, p, data, exclusive, mode)       Command           {0}
FsWriteStream    (ref, p, pieces, exclusive)           CommandReduction  {0}
FsAppend         (ref, p, text)                        Command           {0}
FsAppendStream   (ref, p, lines)                       CommandReduction  {0}
FsMkdir          (ref, *ps, mode)                      Command           {0}
FsRemove         (ref, *ps, tree)                      Command           {0}
FsRemoveIfHolds  (ref, p, text)                        Command           {0}
FsMove           (ref, src, dst, overwrite)            Command           {0}
FsCopy           (ref, src, dst, overwrite, verify)    Command           {0}
FsTouch          (ref, p)                              Command           {0}
FsMakeTemp       (ref, prefix, dir)                    ScalarAction      {0}
===============  ====================================  ================  =======

Every write declares ``mutates`` on slot 0, the mount's ``FsRef``, and a
read only mount raises ``FsReadOnly`` when one runs. The engine does not
order two writes in one ``Parallel``: under an async run they overlap, so
writes that must not interleave go under an ``fs.Lock``. ``FsWriteStream``
and ``FsAppendStream`` fold a stream term in slot 2 into one write.

Paths are relative to the mount, a ``str``, a ``PurePath`` or a term
yielding one (a ``nustd.pathlib.Path``); see ``FsFabric`` for the checks.

A sync run calls the fabric in place. An async run calls it in a thread, and
a stream reads each piece in a thread, so no file call blocks the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, CommandReduction, Nu, ScalarAction, ScalarQuery, StreamQuery
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.null import is_null
from nu.lang.sentinels import UNSET

from .fabric import STEP, FsFabric


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang.runtime import Runtime


__all__ = [
    "FsAppend",
    "FsAppendStream",
    "FsCopy",
    "FsDigest",
    "FsHas",
    "FsHeld",
    "FsLines",
    "FsList",
    "FsMakeTemp",
    "FsMkdir",
    "FsMove",
    "FsOpen",
    "FsReadBytes",
    "FsReadText",
    "FsRemove",
    "FsRemoveIfHolds",
    "FsStat",
    "FsTouch",
    "FsUsage",
    "FsWhere",
    "FsWriteBytes",
    "FsWriteStream",
    "FsWriteText",
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


class FsHeld(ScalarQuery):
    """Who holds the lock on a file, probed without taking it.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the lock file's path in the mount, as ``fs.Lock`` was given it.

    Notes:
        - A lock this process holds is answered from its own table; any
          other is probed with a shared ``lockf``, which a holder's
          exclusive lock refuses. Nothing is taken and no holder is
          disturbed.
        - A lock file whose holder is gone (released, or the process died)
          reads as None, though the file stays naming its last holder.
        - A file system that cannot lock reads as None.

    Yields:
        The holder's record ``{host, pid, what, taken_at}``, ``{}`` for a
        holder that left none, or None when nobody holds it.

    Example:
        data.held("jobs/index.lock")
    """

    def __init__(self, ref: object, p: object) -> None:
        super().__init__(ref_node(ref), p)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        def thunk(rt: Runtime) -> object:
            return fabric_of(ref(rt)).held(p(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.held, await p(rt))

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


# --- writes -----------------------------------------------------------------


_WRITES = Declared(value=frozenset({0}), name="mutates")


class FsWriteText(Command):
    r"""Writes a file's text whole, through a temp moved in place.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount; missing parents are made.
        text: the text, written as UTF-8.
        exclusive: refuse a taken name with ``FileExistsError``, leaving it as
            it was.
        mode: permission bits for the file; None keeps the replaced file's,
            or the process default for a new one.

    Notes:
        - The text goes to a temp file in the same dir, is fsynced, then
          replaces the file in one rename, so a reader sees the old text or
          the new, never half. A crash leaves at most a ``.<name>.*.tmp``.
        - Exclusive, the temp is hard linked in rather than renamed, so two
          racing writers never both win.
        - Without ``exclusive`` the write is idempotent: running it twice
          leaves what running it once does.
        - A read only mount raises ``FsReadOnly``.

    Example:
        data.write_text("notes.md", "# notes\n")
    """

    _mutates = _WRITES

    def __init__(
        self,
        ref: object,
        p: object,
        text: object,
        exclusive: object = False,
        mode: object = None,
    ) -> None:
        super().__init__(ref_node(ref), p, text, exclusive, mode)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _whole_write(children, "text")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _awhole_write(children, "text")


class FsWriteBytes(Command):
    """Writes a file's bytes whole, through a temp moved in place.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount; missing parents are made.
        data: the bytes.
        exclusive: refuse a taken name with ``FileExistsError``.
        mode: permission bits for the file; None keeps the replaced file's.

    Notes:
        - Atomic and exclusive as ``FsWriteText``; idempotent without
          ``exclusive``.

    Example:
        data.write_bytes("cat.png", png)
    """

    _mutates = _WRITES

    def __init__(
        self,
        ref: object,
        p: object,
        data: object,
        exclusive: object = False,
        mode: object = None,
    ) -> None:
        super().__init__(ref_node(ref), p, data, exclusive, mode)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _whole_write(children, "bytes")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _awhole_write(children, "bytes")


def _checked(value: object, kind: str) -> object:
    """Refuse bytes where text is written, and text where bytes are."""
    if kind == "text" and not isinstance(value, str):
        raise TypeError(f"write_text takes a str, got {type(value).__name__}; use write_bytes")
    if kind == "bytes" and not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"write_bytes takes bytes, got {type(value).__name__}; use write_text")
    return value


def _whole_write(children: tuple[Callable, ...], kind: str) -> Callable:
    ref, p, data, exclusive, mode = children

    def thunk(rt: Runtime) -> None:
        fabric = fabric_of(ref(rt))
        fabric.write(
            p(rt),
            _checked(data(rt), kind),
            exclusive=bool(exclusive(rt)),
            mode=optional(mode(rt)),  # type: ignore[arg-type]
        )

    return thunk


def _awhole_write(children: tuple[Callable, ...], kind: str) -> Callable:
    ref, p, data, exclusive, mode = children

    async def athunk(rt: Runtime) -> None:
        fabric = fabric_of(await ref(rt))
        path, value = await p(rt), _checked(await data(rt), kind)
        excl, bits = bool(await exclusive(rt)), optional(await mode(rt))
        await asyncio.to_thread(fabric.write, path, value, exclusive=excl, mode=bits)  # type: ignore[arg-type]

    return athunk


class FsWriteStream(CommandReduction):
    """Writes a stream of byte pieces to a file, moved in place once the stream is drained.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount; missing parents are made.
        pieces: a stream term of ``bytes`` (or ``str``, as UTF-8) pieces,
            such as another file's ``open`` or a blob store's.
        exclusive: refuse a taken name with ``FileExistsError``.

    Notes:
        - A reduction: slot 2 takes the stream. The pieces go to
          ``<p>.part`` in the same dir as they are pulled, never collected;
          the part is fsynced and renamed over ``p`` when the stream ends.
        - A stream that raises removes the part and leaves ``p`` as it was.
        - Exclusive, the part is hard linked in, as ``FsWriteBytes`` does.

    Example:
        data.write_stream("copy.bin", Media.open(bid))
    """

    _mutates = _WRITES
    _reduces = Declared(value=2, name="reduces")

    def __init__(self, ref: object, p: object, pieces: object, exclusive: object = False) -> None:
        super().__init__(ref_node(ref), p, pieces, exclusive)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, pieces, exclusive = children

        def thunk(rt: Runtime) -> None:
            fabric = fabric_of(ref(rt))
            part = fabric.open_part(p(rt), exclusive=bool(exclusive(rt)))
            try:
                for piece in sync_iter(pieces(rt)):
                    part.write(piece)
            except BaseException:
                part.abort()
                raise
            part.commit()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, pieces, exclusive = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            path, excl = await p(rt), bool(await exclusive(rt))
            part = await asyncio.to_thread(fabric.open_part, path, exclusive=excl)
            try:
                async for piece in aiter_any(await pieces(rt)):
                    await asyncio.to_thread(part.write, piece)
            except BaseException:
                await asyncio.to_thread(part.abort)
                raise
            await asyncio.to_thread(part.commit)

        return athunk


class FsAppend(Command):
    r"""Adds text to the end of a file, made when missing.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount; missing parents are made.
        text: the text, written as UTF-8 exactly as given, no newline added.
            Bytes are written as they are.

    Notes:
        - One ``O_APPEND`` write, so lines appended by several processes at
          once do not tear on a local disk. NFS does not promise that.
        - Not idempotent: running it twice adds the text twice.

    Example:
        data.append("app.log", "started\n")
    """

    _mutates = _WRITES

    def __init__(self, ref: object, p: object, text: object) -> None:
        super().__init__(ref_node(ref), p, text)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, text = children

        def thunk(rt: Runtime) -> None:
            fabric_of(ref(rt)).append(p(rt), text(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, text = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            await asyncio.to_thread(fabric.append, await p(rt), await text(rt))

        return athunk


class FsAppendStream(CommandReduction):
    r"""Adds a stream of lines to the end of a file, through one append handle.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount; missing parents are made.
        lines: a stream term of ``str`` lines; each is written with a
            ``"\n"`` after it.

    Notes:
        - A reduction: slot 2 takes the stream. The file is opened once and
          each line written as it is pulled, one ``O_APPEND`` write a line.
        - A stream that raises leaves the lines written so far.

    Example:
        data.append_stream("app.log", nu.Map(events, render))
    """

    _mutates = _WRITES
    _reduces = Declared(value=2, name="reduces")

    def __init__(self, ref: object, p: object, lines: object) -> None:
        super().__init__(ref_node(ref), p, lines)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, lines = children

        def thunk(rt: Runtime) -> None:
            fd = fabric_of(ref(rt)).open_append(p(rt))
            try:
                for line in sync_iter(lines(rt)):
                    write_line(fd, line)
            finally:
                os.close(fd)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, lines = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            fd = await asyncio.to_thread(fabric.open_append, await p(rt))
            try:
                async for line in aiter_any(await lines(rt)):
                    await asyncio.to_thread(write_line, fd, line)
            finally:
                os.close(fd)

        return athunk


def write_line(fd: int, line: object) -> None:
    """One line and its newline, in one write."""
    if not isinstance(line, str):
        raise TypeError(f"append_stream takes str lines, got {type(line).__name__}")
    data = memoryview((line + "\n").encode("utf-8"))
    while data:
        data = data[os.write(fd, data) :]


# --- dirs and entries -------------------------------------------------------


class FsMkdir(Command):
    """Makes dirs, each with its parents; one already there is left as it is.

    Args:
        ref: the mount slot, an ``FsRef``.
        *ps: the dirs' paths in the mount.
        mode: permission bits for each dir made; None for the process
            default.

    Notes:
        - Variadic: the number of paths is the ``count`` field, and ``mode``
          is the child after them.
        - Idempotent: running it twice leaves what running it once does.
        - A file in the way raises ``FileExistsError``.

    Example:
        data.mkdir("logs", "cache/thumbs")
    """

    _mutates = _WRITES

    def __init__(self, ref: object, *ps: object, mode: object = None) -> None:
        super().__init__(ref_node(ref), *ps, mode)
        self.count = len(ps)

    def _config_slots(self) -> frozenset[int]:
        """The ``mode`` child's slot, past the paths."""
        return frozenset({self.count + 1})

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, *ps, mode = children

        def thunk(rt: Runtime) -> None:
            fabric = fabric_of(ref(rt))
            fabric.mkdir(*(p(rt) for p in ps), mode=optional(mode(rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, *ps, mode = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            paths = [await p(rt) for p in ps]
            bits = optional(await mode(rt))
            await asyncio.to_thread(fabric.mkdir, *paths, mode=bits)  # type: ignore[arg-type]

        return athunk


class FsRemove(Command):
    """Removes files, links and dirs; a missing path is a no-op.

    Args:
        ref: the mount slot, an ``FsRef``.
        *ps: the paths in the mount.
        tree: remove a dir with all it holds. Off, only an empty dir goes
            and a full one raises ``OSError``.

    Notes:
        - A link is removed as the link; its target is left alone.
        - The mount itself is refused with ``PermissionError``.
        - Variadic like ``FsMkdir``: ``count`` paths, then ``tree``.
        - Idempotent: running it twice leaves what running it once does.

    Example:
        data.remove("cache", tree=True)
    """

    _mutates = _WRITES

    def __init__(self, ref: object, *ps: object, tree: object = False) -> None:
        super().__init__(ref_node(ref), *ps, tree)
        self.count = len(ps)

    def _config_slots(self) -> frozenset[int]:
        """The ``tree`` child's slot, past the paths."""
        return frozenset({self.count + 1})

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, *ps, tree = children

        def thunk(rt: Runtime) -> None:
            fabric = fabric_of(ref(rt))
            fabric.remove(*(p(rt) for p in ps), tree=bool(tree(rt)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, *ps, tree = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            paths = [await p(rt) for p in ps]
            await asyncio.to_thread(fabric.remove, *paths, tree=bool(await tree(rt)))

        return athunk


class FsRemoveIfHolds(Command):
    """Removes a file only while it holds exactly the given text.

    For a file a process wrote to say it owns something (a pid file, a
    claim): the owner removes it on the way out, and a later owner's file,
    holding other text, is kept.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.
        text: what the file must hold to be removed.

    Notes:
        - The read, compare and unlink run under the file's ``lockf`` lock,
          so two removers never race. When another process holds that lock
          the file is live and is kept. A file system that cannot lock goes
          on without it.
        - A missing file is a no-op.

    Example:
        data.remove_if_holds("owner", "red 1234")
    """

    _mutates = _WRITES

    def __init__(self, ref: object, p: object, text: object) -> None:
        super().__init__(ref_node(ref), p, text)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, text = children

        def thunk(rt: Runtime) -> None:
            fabric_of(ref(rt)).remove_if_holds(p(rt), text(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p, text = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            await asyncio.to_thread(fabric.remove_if_holds, await p(rt), await text(rt))

        return athunk


class FsMove(Command):
    """Moves a file, link or dir within the mount.

    Args:
        ref: the mount slot, an ``FsRef``.
        src: the path to move; a link moves as the link.
        dst: where it goes. A ``str`` ending in ``/`` means into that dir,
            keeping the name; the dir is made when missing, as are the
            parents of any other ``dst``.
        overwrite: replace what sits at ``dst``. Off, a taken ``dst`` raises
            ``FileExistsError``.

    Notes:
        - One rename on one device. Without ``overwrite`` a file is hard
          linked in and the source unlinked, so a racing writer at ``dst``
          is never clobbered; a dir is checked, then renamed.
        - Across devices (a mount inside the mount) the entry is copied,
          then the source removed.
        - The mount itself is refused with ``PermissionError``.

    Example:
        data.move("inbox/a.txt", "done/")
    """

    _mutates = _WRITES

    def __init__(self, ref: object, src: object, dst: object, overwrite: object = False) -> None:
        super().__init__(ref_node(ref), src, dst, overwrite)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, src, dst, overwrite = children

        def thunk(rt: Runtime) -> None:
            fabric_of(ref(rt)).move(src(rt), dst(rt), overwrite=bool(overwrite(rt)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, src, dst, overwrite = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            args = (await src(rt), await dst(rt))
            await asyncio.to_thread(fabric.move, *args, overwrite=bool(await overwrite(rt)))

        return athunk


class FsCopy(Command):
    """Copies a file, its data and metadata, within the mount.

    Args:
        ref: the mount slot, an ``FsRef``.
        src: the file to copy; a link is followed.
        dst: where the copy goes; a ``str`` ending in ``/`` means into that
            dir, keeping the name.
        overwrite: replace what sits at ``dst``. Off, a taken ``dst`` raises
            ``FileExistsError``.
        verify: compare the sha256 of source and copy before the copy is
            moved in; a mismatch raises ``OSError`` and leaves ``dst`` as it
            was.

    Notes:
        - ``shutil.copy2`` into a temp beside ``dst``, then moved in whole,
          so a reader never sees half a copy.
        - Files only: a dir raises ``IsADirectoryError``.
        - With ``overwrite`` it is idempotent.

    Example:
        data.copy("cat.png", "backup/", verify=True)
    """

    _mutates = _WRITES

    def __init__(
        self,
        ref: object,
        src: object,
        dst: object,
        overwrite: object = False,
        verify: object = False,
    ) -> None:
        super().__init__(ref_node(ref), src, dst, overwrite, verify)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, src, dst, overwrite, verify = children

        def thunk(rt: Runtime) -> None:
            fabric = fabric_of(ref(rt))
            fabric.copy(src(rt), dst(rt), overwrite=bool(overwrite(rt)), verify=bool(verify(rt)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, src, dst, overwrite, verify = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            args = (await src(rt), await dst(rt))
            flags = {"overwrite": bool(await overwrite(rt)), "verify": bool(await verify(rt))}
            await asyncio.to_thread(fabric.copy, *args, **flags)

        return athunk


class FsTouch(Command):
    """Makes a file when missing, with its parents, and sets its mtime to now.

    Args:
        ref: the mount slot, an ``FsRef``.
        p: the file's path in the mount.

    Notes:
        - An existing file keeps its bytes; only its times change.

    Example:
        data.touch("ready")
    """

    _mutates = _WRITES

    def __init__(self, ref: object, p: object) -> None:
        super().__init__(ref_node(ref), p)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        def thunk(rt: Runtime) -> None:
            fabric_of(ref(rt)).touch(p(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, p = children

        async def athunk(rt: Runtime) -> None:
            fabric = fabric_of(await ref(rt))
            await asyncio.to_thread(fabric.touch, await p(rt))

        return athunk


class FsMakeTemp(ScalarAction):
    """Makes a fresh, empty dir inside the mount and yields its path.

    Args:
        ref: the mount slot, an ``FsRef``.
        prefix: the dir's name prefix.
        dir: the dir to make it in, made when missing; ``"."`` for the
            mount itself.

    Notes:
        - The name is minted when it runs, never when the tree is built, so
          each run makes its own.
        - Nothing removes it: remove it with ``FsRemove(..., tree=True)``,
          or mount ``fs.tmp`` for a dir that goes at exit.

    Yields:
        The new dir's ``PurePosixPath`` relative to the mount.

    Example:
        nu.let(lambda d: (data.file(d) / "in.txt").write_text("..."), d=data.make_temp("job-"))
    """

    _mutates = _WRITES

    def __init__(self, ref: object, prefix: object = "tmp-", dir: object = ".") -> None:
        super().__init__(ref_node(ref), prefix, dir)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, prefix, where = children

        def thunk(rt: Runtime) -> object:
            return fabric_of(ref(rt)).make_temp(prefix(rt), where(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref, prefix, where = children

        async def athunk(rt: Runtime) -> object:
            fabric = fabric_of(await ref(rt))
            return await asyncio.to_thread(fabric.make_temp, await prefix(rt), await where(rt))

        return athunk
