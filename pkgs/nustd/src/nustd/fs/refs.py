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
from nu.lang import Nu, ScalarQuery
from nu.lang.null import Null, is_null
from nu.lang.sentinels import UNSET

from .fabric import STEP, FsFabric
from .interactions import (
    FsDigest,
    FsHas,
    FsLines,
    FsList,
    FsOpen,
    FsReadBytes,
    FsReadText,
    FsStat,
    FsUsage,
    FsWhere,
)


if TYPE_CHECKING:
    from collections.abc import Callable

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

    def list(
        self,
        p: object = ".",
        *,
        pattern: object = "*",
        recursive: object = False,
        kind: object = None,
    ) -> FsList:
        """The entries of the dir ``p``, a lazy stream; see ``FsList``."""
        return FsList(self, p, pattern, recursive, kind)

    def open(self, p: object, start: object = 0, end: object = None, step: object = STEP) -> FsOpen:
        """The file's bytes as a lazy stream of pieces; see ``FsOpen``."""
        return FsOpen(self, p, start, end, step)

    def lines(self, p: object, encoding: object = "utf-8") -> FsLines:
        """The file's lines as a lazy stream; see ``FsLines``."""
        return FsLines(self, p, encoding)


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

    def list(
        self, *, pattern: object = "*", recursive: object = False, kind: object = None
    ) -> FsList:
        """The entries of this dir, a lazy stream; see ``FsList``."""
        return FsList(self._fs, self._path, pattern, recursive, kind)

    def open(self, start: object = 0, end: object = None, step: object = STEP) -> FsOpen:
        """The file's bytes as a lazy stream of pieces; see ``FsOpen``."""
        return FsOpen(self._fs, self._path, start, end, step)

    def lines(self, encoding: object = "utf-8") -> FsLines:
        """The file's lines as a lazy stream; see ``FsLines``."""
        return FsLines(self._fs, self._path, encoding)


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
