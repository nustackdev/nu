"""FsRef, the mount every fs term reaches the disk through, and FileRef, a path on it.

``FsRef`` is the Ref: a ``FabricRef`` over ``FsFabric``, tagged so several
mounts live in one tree. ``FileRef`` is not a Ref and not a term. It is a
plain handle holding a mount and a path, and every term it builds lands on
the mount's ``FsRef``, so the effect checks see one channel per mount, never
one per file.
"""

from __future__ import annotations

import os
from pathlib import PurePath, PurePosixPath
from typing import TYPE_CHECKING, NoReturn, cast

from nu.context import FabricRef
from nu.lang import Literal, Nu, ScalarQuery
from nu.lang.null import Null, is_null
from nu.lang.sentinels import UNSET

from .fabric import STEP, FsFabric
from .interactions import (
    FsAppend,
    FsAppendStream,
    FsCopy,
    FsDigest,
    FsHas,
    FsHeld,
    FsLines,
    FsList,
    FsMakeTemp,
    FsMkdir,
    FsMove,
    FsOpen,
    FsReadBytes,
    FsReadText,
    FsRemove,
    FsRemoveIfHolds,
    FsStat,
    FsTouch,
    FsUsage,
    FsWhere,
    FsWriteBytes,
    FsWriteStream,
    FsWriteText,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Iterator
    from nu.forms.primitives import Bool
    from nu.lang.runtime import Runtime
    from nustd.pathlib import Path


__all__ = ["FileRef", "FsRef"]


def check_tag(tag: object) -> str | Nu:
    """A mount tag: a ``str`` (``""`` for the untagged mount) or a term computing one."""
    if isinstance(tag, (str, Nu)):
        return tag
    raise TypeError(f"an fs mount tag is a str or a term, got {tag!r}")


class FsRef(FabricRef):
    """A mount: the ``FsFabric`` bound under its tag, and the terms that reach it.

    Every fs term holds this ref in slot 0, so one ``FsRef`` held in a module
    serves any number of terms and trees, and the writes to one mount are
    seen as writes to one channel.

    Args:
        tag: the tag the mount binds under, ``""`` for the untagged one, or
            a term yielding it.

    Notes:
        - Reading it is a lookup and nothing else: the bound ``FsFabric``, or
          NULL when no mount is bound under the tag. A tagged ref never
          falls back to the untagged mount, so a write meant for ``"data"``
          never lands in some other dir.
        - ``ref / "a"`` and ``ref.file("a")`` make a ``FileRef``, a path on
          this mount carrying the same verbs.
        - ``exists()`` asks whether a mount is bound; ``has(p)`` asks whether
          something sits at ``p``.
        - Writes declare ``mutates`` on this ref, but the engine does not
          order two of them in one ``Parallel``; guard a file that must not
          see interleaved writes with ``fs.Lock``.

    Yields:
        The bound ``FsFabric``, or NULL when nothing is bound under the tag.

    Example:
        data = fs.FsRef("data")

        app = fs.mount("./data", tag="data", body=data.read_text("notes.md"))
    """

    fabric = FsFabric

    def __init__(self, tag: str | Nu = "") -> None:
        # Children: [fabric, tag].
        super().__init__(None, check_tag(tag))

    @property
    def tag(self) -> Nu:
        """The tag child, a term."""
        return cast("Nu", self._children[1])

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, tag_of = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            return _lookup(rt, fabric(rt), tag_of(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric, tag_of = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            return _lookup(rt, await fabric(rt), await tag_of(rt))

        return athunk

    def exists(self) -> Bool:
        """Whether a mount is bound under this ref's tag, as a ``Bool``."""
        from nu.forms.primitives import Bool

        return Bool(_MountBound(self))

    # --- paths --------------------------------------------------------------

    def file(self, p: object) -> FileRef:
        """A ``FileRef`` for ``p`` on this mount."""
        return FileRef(self, p)

    def __truediv__(self, p: object) -> FileRef:
        """``ref / "a"``: a ``FileRef`` for ``a`` on this mount."""
        return FileRef(self, p)

    # --- queries ------------------------------------------------------------

    def read_text(
        self, p: object, encoding: object = "utf-8", default: object = UNSET
    ) -> FsReadText:
        """The file's text; see ``FsReadText``."""
        return FsReadText(self, p, encoding, default)

    def read_bytes(
        self, p: object, start: object = 0, end: object = None, default: object = UNSET
    ) -> FsReadBytes:
        """The file's bytes in ``[start, end)``; see ``FsReadBytes``."""
        return FsReadBytes(self, p, start, end, default)

    def stat(self, p: object) -> FsStat:
        """The entry at ``p``, or None; see ``FsStat``."""
        return FsStat(self, p)

    def has(self, p: object, kind: object = None) -> FsHas:
        """Whether something (of ``kind``) sits at ``p``; see ``FsHas``."""
        return FsHas(self, p, kind)

    def usage(self) -> FsUsage:
        """The mount's file system ``{total, free, used}``; see ``FsUsage``."""
        return FsUsage(self)

    def where(self, p: object = ".") -> FsWhere:
        """The absolute path of ``p``; see ``FsWhere``."""
        return FsWhere(self, p)

    def digest(self, p: object, algo: object = "sha256") -> FsDigest:
        """The hex digest of the file; see ``FsDigest``."""
        return FsDigest(self, p, algo)

    def held(self, p: object) -> FsHeld:
        """Who holds the lock on ``p``, or None; see ``FsHeld``."""
        return FsHeld(self, p)

    def list(
        self,
        p: object = ".",
        *,
        pattern: object = "*",
        recursive: object = False,
        kind: object = None,
    ) -> Iterator:
        """The entries of the dir ``p``, a lazy stream; see ``FsList``."""
        from nu.forms import Iterator

        return Iterator(FsList(self, p, pattern, recursive, kind))

    def open(
        self, p: object, start: object = 0, end: object = None, step: object = STEP
    ) -> Iterator:
        """The file's bytes as a lazy stream of pieces; see ``FsOpen``."""
        from nu.forms import Iterator

        return Iterator(FsOpen(self, p, start, end, step))

    def lines(self, p: object, encoding: object = "utf-8") -> Iterator:
        """The file's lines as a lazy stream; see ``FsLines``."""
        from nu.forms import Iterator

        return Iterator(FsLines(self, p, encoding))

    # --- writes -------------------------------------------------------------

    def write_text(
        self, p: object, text: object, *, exclusive: object = False, mode: object = None
    ) -> FsWriteText:
        """Write the file's text whole, atomically; see ``FsWriteText``."""
        return FsWriteText(self, p, text, exclusive, mode)

    def write_bytes(
        self, p: object, data: object, *, exclusive: object = False, mode: object = None
    ) -> FsWriteBytes:
        """Write the file's bytes whole, atomically; see ``FsWriteBytes``."""
        return FsWriteBytes(self, p, data, exclusive, mode)

    def write_stream(
        self, p: object, pieces: object, *, exclusive: object = False
    ) -> FsWriteStream:
        """Write a stream of pieces to the file, moved in when drained; see ``FsWriteStream``."""
        return FsWriteStream(self, p, pieces, exclusive)

    def append(self, p: object, text: object) -> FsAppend:
        """Add text to the end of the file; see ``FsAppend``."""
        return FsAppend(self, p, text)

    def append_stream(self, p: object, lines: object) -> FsAppendStream:
        """Add a stream of lines to the end of the file; see ``FsAppendStream``."""
        return FsAppendStream(self, p, lines)

    def mkdir(self, *ps: object, mode: object = None) -> FsMkdir:
        """Make each dir with its parents; see ``FsMkdir``."""
        return FsMkdir(self, *ps, mode=mode)

    def remove(self, *ps: object, tree: object = False) -> FsRemove:
        """Remove each path, a missing one skipped; see ``FsRemove``."""
        return FsRemove(self, *ps, tree=tree)

    def remove_if_holds(self, p: object, text: object) -> FsRemoveIfHolds:
        """Remove the file only while it holds ``text``; see ``FsRemoveIfHolds``."""
        return FsRemoveIfHolds(self, p, text)

    def move(self, src: object, dst: object, *, overwrite: object = False) -> FsMove:
        """Move ``src`` to ``dst``, ``"dir/"`` meaning into it; see ``FsMove``."""
        return FsMove(self, src, self._own(dst), overwrite)

    def copy(
        self, src: object, dst: object, *, overwrite: object = False, verify: object = False
    ) -> FsCopy:
        """Copy the file ``src`` to ``dst``; see ``FsCopy``."""
        return FsCopy(self, src, self._own(dst), overwrite, verify)

    def touch(self, p: object) -> FsTouch:
        """Make the file when missing and set its mtime; see ``FsTouch``."""
        return FsTouch(self, p)

    def make_temp(self, prefix: object = "tmp-", dir: object = ".") -> FsMakeTemp:
        """Make a fresh dir in the mount and yield its path; see ``FsMakeTemp``."""
        return FsMakeTemp(self, prefix, dir)

    def _own(self, p: object) -> object:
        """A path argument, a ``FileRef`` on this mount taken as its path."""
        if not isinstance(p, FileRef):
            return p
        if not _same_mount(self, p.fs):
            raise ValueError(f"{p!r} is on another mount; move and copy stay within one")
        return p.p


def _same_mount(a: FsRef, b: FsRef) -> bool:
    """Whether two refs name one mount; a computed tag is taken at its word."""
    if a is b:
        return True
    ta, tb = a.tag, b.tag
    if isinstance(ta, Literal) and isinstance(tb, Literal):
        return ta.value == tb.value
    return True


def _lookup(rt: Runtime, fabric: object, tag: object) -> object:
    """The mount bound under exactly ``tag``, or NULL hinting the tag."""
    if not isinstance(tag, str):
        raise TypeError(f"an fs mount tag is a str, got {tag!r}")
    fabrics = rt.ctx.fabrics
    kind = cast("type", fabric)
    if not tag:
        return fabrics.get(kind) if fabrics.has(kind) else Null()
    if not fabrics.has(kind, tag):
        return Null(tag)
    found = fabrics.get(kind, tag)
    # Resolution falls back to the untagged binding; that one is not ours.
    if fabrics.has(kind) and fabrics.get(kind) is found:
        return Null(tag)
    return found


class _MountBound(ScalarQuery):
    """Whether its ``FsRef`` reads a bound mount rather than NULL.

    Args:
        ref: the ``FsRef`` to read.

    Yields:
        True or False.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        def thunk(rt: Runtime) -> bool:
            return not is_null(ref(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref,) = children

        async def athunk(rt: Runtime) -> bool:
            return not is_null(await ref(rt))

        return athunk


# --- FileRef ----------------------------------------------------------------


class FileRef:
    """A path on a mount: a plain, immutable handle carrying the mount's verbs.

    Not a Ref and not a term. Every term it builds is the mount's own, with
    the path filled in, so ``(data / "a.txt").read_text()`` and
    ``data.read_text("a.txt")`` are the same term.

    Args:
        fs: the mount, an ``FsRef``.
        p: the path on it, a relative ``str``, a ``PurePath`` or a term
            yielding one.

    Notes:
        - ``file / "b"`` extends the path. Two plain parts join now; a term
          part joins when the term runs.
        - ``file.path`` is the path as a ``nustd.pathlib.Path`` form, for its
          lexical ops (``.name``, ``.suffix``, ``.with_suffix(...)``).
        - Picklable, so it travels with a tree to another process.

    Example:
        notes = fs.FsRef("data") / "notes"
        nu.Sequential(notes.mkdir(), (notes / "a.md").write_text("hi"))
    """

    __slots__ = ("_fs", "_path")

    _fs: FsRef
    _path: object

    def __init__(self, fs: FsRef, p: object) -> None:
        if not isinstance(fs, FsRef):
            raise TypeError(f"a FileRef's mount is an FsRef, got {fs!r}")
        object.__setattr__(self, "_fs", fs)
        object.__setattr__(self, "_path", _path_value(p))

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError(f"a FileRef is immutable; build another with file / {value!r}")

    def __delattr__(self, name: str) -> NoReturn:
        raise AttributeError("a FileRef is immutable")

    def __reduce__(self) -> tuple[type[FileRef], tuple[FsRef, object]]:
        return (FileRef, (self._fs, self._path))

    def __repr__(self) -> str:
        shown = self._path.as_posix() if isinstance(self._path, PurePath) else self._path
        return f"FileRef({shown!r})"

    @property
    def fs(self) -> FsRef:
        """The mount this path is on."""
        return self._fs

    @property
    def p(self) -> object:
        """The path as the terms take it: a ``PurePosixPath`` or a term."""
        return self._path

    @property
    def path(self) -> Path:
        """The path as a ``nustd.pathlib.Path`` form."""
        from nustd.pathlib import Path

        if isinstance(self._path, Path):
            return self._path
        return Path.of(self._path)  # type: ignore[arg-type]

    def __truediv__(self, other: object) -> FileRef:
        """``file / "b"``: the path one part further."""
        return FileRef(self._fs, _join(self._path, other))

    # --- queries ------------------------------------------------------------

    def read_text(self, encoding: object = "utf-8", default: object = UNSET) -> FsReadText:
        """The file's text; see ``FsReadText``."""
        return FsReadText(self._fs, self._path, encoding, default)

    def read_bytes(
        self, start: object = 0, end: object = None, default: object = UNSET
    ) -> FsReadBytes:
        """The file's bytes in ``[start, end)``; see ``FsReadBytes``."""
        return FsReadBytes(self._fs, self._path, start, end, default)

    def stat(self) -> FsStat:
        """The entry at this path, or None; see ``FsStat``."""
        return FsStat(self._fs, self._path)

    def has(self, kind: object = None) -> FsHas:
        """Whether something (of ``kind``) sits at this path; see ``FsHas``."""
        return FsHas(self._fs, self._path, kind)

    def exists(self) -> FsHas:
        """Whether something sits at this path: ``has()``."""
        return FsHas(self._fs, self._path)

    def where(self) -> FsWhere:
        """The absolute path; see ``FsWhere``."""
        return FsWhere(self._fs, self._path)

    def digest(self, algo: object = "sha256") -> FsDigest:
        """The hex digest of the file; see ``FsDigest``."""
        return FsDigest(self._fs, self._path, algo)

    def held(self) -> FsHeld:
        """Who holds the lock on this file, or None; see ``FsHeld``."""
        return FsHeld(self._fs, self._path)

    def list(
        self, *, pattern: object = "*", recursive: object = False, kind: object = None
    ) -> Iterator:
        """The entries of this dir, a lazy stream; see ``FsList``."""
        from nu.forms import Iterator

        return Iterator(FsList(self._fs, self._path, pattern, recursive, kind))

    def open(self, start: object = 0, end: object = None, step: object = STEP) -> Iterator:
        """The file's bytes as a lazy stream of pieces; see ``FsOpen``."""
        from nu.forms import Iterator

        return Iterator(FsOpen(self._fs, self._path, start, end, step))

    def lines(self, encoding: object = "utf-8") -> Iterator:
        """The file's lines as a lazy stream; see ``FsLines``."""
        from nu.forms import Iterator

        return Iterator(FsLines(self._fs, self._path, encoding))

    # --- writes -------------------------------------------------------------

    def write_text(
        self, text: object, *, exclusive: object = False, mode: object = None
    ) -> FsWriteText:
        """Write the file's text whole, atomically; see ``FsWriteText``."""
        return FsWriteText(self._fs, self._path, text, exclusive, mode)

    def write_bytes(
        self, data: object, *, exclusive: object = False, mode: object = None
    ) -> FsWriteBytes:
        """Write the file's bytes whole, atomically; see ``FsWriteBytes``."""
        return FsWriteBytes(self._fs, self._path, data, exclusive, mode)

    def write_stream(self, pieces: object, *, exclusive: object = False) -> FsWriteStream:
        """Write a stream of pieces to the file, moved in when drained; see ``FsWriteStream``."""
        return FsWriteStream(self._fs, self._path, pieces, exclusive)

    def append(self, text: object) -> FsAppend:
        """Add text to the end of the file; see ``FsAppend``."""
        return FsAppend(self._fs, self._path, text)

    def append_stream(self, lines: object) -> FsAppendStream:
        """Add a stream of lines to the end of the file; see ``FsAppendStream``."""
        return FsAppendStream(self._fs, self._path, lines)

    def mkdir(self, *, mode: object = None) -> FsMkdir:
        """Make this dir with its parents; see ``FsMkdir``."""
        return FsMkdir(self._fs, self._path, mode=mode)

    def remove(self, *, tree: object = False) -> FsRemove:
        """Remove this path, a no-op when missing; see ``FsRemove``."""
        return FsRemove(self._fs, self._path, tree=tree)

    def remove_if_holds(self, text: object) -> FsRemoveIfHolds:
        """Remove the file only while it holds ``text``; see ``FsRemoveIfHolds``."""
        return FsRemoveIfHolds(self._fs, self._path, text)

    def move(self, dst: object, *, overwrite: object = False) -> FsMove:
        """Move this entry to ``dst``, ``"dir/"`` meaning into it; see ``FsMove``."""
        return self._fs.move(self._path, dst, overwrite=overwrite)

    def copy(self, dst: object, *, overwrite: object = False, verify: object = False) -> FsCopy:
        """Copy this file to ``dst``; see ``FsCopy``."""
        return self._fs.copy(self._path, dst, overwrite=overwrite, verify=verify)

    def touch(self) -> FsTouch:
        """Make the file when missing and set its mtime; see ``FsTouch``."""
        return FsTouch(self._fs, self._path)

    def make_temp(self, prefix: object = "tmp-") -> FsMakeTemp:
        """Make a fresh dir inside this one and yield its path; see ``FsMakeTemp``."""
        return FsMakeTemp(self._fs, prefix, self._path)


def _path_value(p: object) -> object:
    """A path argument as a FileRef holds it: a ``PurePosixPath``, or the term as given."""
    if isinstance(p, Nu):
        return p
    if isinstance(p, PurePath):
        return PurePosixPath(p.as_posix())
    if isinstance(p, str):
        return PurePosixPath(p)
    if isinstance(p, os.PathLike):
        return PurePosixPath(os.fspath(p))  # type: ignore[arg-type]
    raise TypeError(f"an fs path is a str, a PurePath or a term, got {p!r}")


def _join(head: object, tail: object) -> object:
    """``head / tail``: joined now when both are plain, by a ``_Join`` term otherwise."""
    tail = _path_value(tail)
    if isinstance(head, PurePath) and isinstance(tail, PurePath):
        return head / tail
    return _Join(head, tail)


class _Join(ScalarQuery):
    """Two path parts joined when the tree runs: ``PurePosixPath(head) / tail``.

    Args:
        head: the path so far, a ``PurePath``, a ``str`` or a term.
        tail: the part to add, the same.

    Yields:
        A ``PurePosixPath``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        head, tail = children

        def thunk(rt: Runtime) -> PurePosixPath:
            return _joined(head(rt), tail(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        head, tail = children

        async def athunk(rt: Runtime) -> PurePosixPath:
            return _joined(await head(rt), await tail(rt))

        return athunk


def _joined(head: object, tail: object) -> PurePosixPath:
    parts = []
    for part in (head, tail):
        if isinstance(part, PurePath):
            parts.append(part.as_posix())
        elif isinstance(part, str):
            parts.append(part)
        else:
            raise TypeError(f"an fs path part is a str or a PurePath, got {part!r}")
    return PurePosixPath(*parts)
