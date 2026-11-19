"""FsFabric: one directory of the real file system, bound as a mount for the span of a tree.

The fabric does the ``os`` / ``shutil`` work itself, as plain sync methods.
The interactions call them in place under a sync run and through
``asyncio.to_thread`` under an async one, so no file call blocks the event
loop. There is no backend protocol and no in-memory twin: a test mounts a
``tmp_path``.

Every path a method takes is relative to the mount, a ``str`` or a
``PurePath``. It is cut into parts lexically, never handed to the OS with a
``..`` in it, and checked against the mount's ``follow`` rule:

==========  ==============================================================
follow      a symlink on the path is
==========  ==============================================================
"inside"    allowed when it resolves inside the mount (the default)
"never"     refused, wherever it points
"any"       followed wherever it points
==========  ==============================================================

An absolute path, a ``..`` past the mount, or a symlink the rule refuses
raises ``FsEscape``.
"""

from __future__ import annotations

import asyncio
import fnmatch
import hashlib
import os
import shutil
import stat as st
import tempfile
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING

from nu.context.fabric import Fabric

from .errors import FsEscape, FsReadOnly


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang.runtime import Context


__all__ = ["FOLLOW", "KINDS", "STEP", "FsFabric"]


#: Bytes per piece a stream reads, unless told otherwise.
STEP = 1 << 20

#: The ``follow`` rules a mount takes.
FOLLOW = frozenset({"inside", "never", "any"})

#: What an entry's ``kind`` can be.
KINDS = frozenset({"file", "dir", "link", "other"})


class FsFabric(Fabric):
    """A directory held as a mount for the span of a ``Provide``.

    The tree carries the options, not an open directory: the mount is
    resolved when the bracket is entered, so a tree sent to another process
    mounts there.

    Args:
        path: the directory to mount. With ``temp``, the directory the temp
            dir is made in; None for the system's temp dir.
        readonly: refuse every write with ``FsReadOnly``.
        create: make the directory, with its parents, when it is missing.
            Off, a missing one raises ``FileNotFoundError`` at entry.
        mode: permission bits for the directory when it is made; None for
            the process default.
        follow: the symlink rule, ``"inside"``, ``"never"`` or ``"any"``.
        temp: mount a fresh temp dir rather than ``path``.
        prefix: the temp dir's name prefix.
        keep: leave the temp dir behind at exit rather than removing it.

    Notes:
        - The mount is resolved once, at entry, symlinks and all, so a mount
          given through a link (``/tmp`` on macOS) is checked against its
          real place.
        - A sync run sets up and tears down in place; an async run does both
          in a thread.
        - Paths are checked when an op runs, and nothing stops a process
          outside the tree from swapping a dir for a link in between.
    """

    def __init__(
        self,
        *,
        path: str | os.PathLike[str] | None = None,
        readonly: bool = False,
        create: bool = True,
        mode: int | None = None,
        follow: str = "inside",
        temp: bool = False,
        prefix: str = "nu-",
        keep: bool = False,
    ) -> None:
        check_follow(follow)
        if path is None and not temp:
            raise ValueError("an fs mount needs a path; use fs.tmp() for a temp dir")
        self.path = None if path is None else os.fspath(path)
        self.readonly = bool(readonly)
        self.create = bool(create)
        self.mode = mode
        self.follow = follow
        self.temp = bool(temp)
        self.prefix = prefix
        self.keep = bool(keep)
        self._root: str | None = None

    # --- lifecycle ----------------------------------------------------------

    def setup(self, ctx: Context) -> None:
        """Resolve the mount, making it when asked to."""
        if self.temp:
            where = Path(tempfile.mkdtemp(prefix=self.prefix, dir=self.path))
            if self.mode is not None:
                where.chmod(self.mode)
        else:
            where = Path(self.path or "").absolute()
            if not os.path.lexists(where):
                if not self.create:
                    raise FileNotFoundError(
                        f"fs mount {str(where)!r} does not exist and create is off"
                    )
                where.mkdir(parents=True, exist_ok=True)
                if self.mode is not None:
                    where.chmod(self.mode)
        real = os.path.realpath(where)
        if not Path(real).is_dir():
            raise NotADirectoryError(f"fs mount {str(where)!r} is not a directory")
        self._root = real

    def cleanup(self) -> None:
        """Remove a temp mount unless it is kept."""
        root, self._root = self._root, None
        if root is not None and self.temp and not self.keep:
            shutil.rmtree(root, ignore_errors=True)

    async def asetup(self, ctx: Context) -> None:
        """``setup``, off the event loop."""
        await asyncio.to_thread(self.setup, ctx)

    async def acleanup(self) -> None:
        """``cleanup``, off the event loop."""
        await asyncio.to_thread(self.cleanup)

    @property
    def root(self) -> str:
        """The mount's real absolute path. Raises outside the bracket that bound it."""
        if self._root is None:
            raise RuntimeError("the fs mount is not open: use it inside the With that binds it")
        return self._root

    # --- paths --------------------------------------------------------------

    def resolve(self, p: object, *, leaf: bool = True) -> str:
        """The absolute path of ``p`` inside the mount, checked against ``follow``.

        Args:
            p: a path relative to the mount, ``str`` or ``PurePath``.
            leaf: also check the last part. Off for an op on the entry
                itself (stat, remove, move), so a link is seen as a link.

        Raises:
            FsEscape: ``p`` would leave the mount.
        """
        root = self.root
        parts = split(p)
        full = str(Path(root, *parts))
        if self.follow == "any":
            return full
        checked = parts if leaf else parts[:-1]
        if self.follow == "never":
            here = Path(root)
            for part in checked:
                here /= part
                if here.is_symlink():
                    raise FsEscape(f"{_shown(p)} goes through a symlink and the mount follows none")
            return full
        real = os.path.realpath(Path(root, *checked))
        if real != root and not real.startswith(root.rstrip(os.sep) + os.sep):
            raise FsEscape(f"{_shown(p)} resolves outside the mount")
        return full

    def relative(self, full: str) -> PurePosixPath:
        """``full``, a path under the mount, as the mount sees it."""
        return PurePosixPath(os.path.relpath(full, self.root).replace(os.sep, "/"))

    def writable(self) -> None:
        """Raise ``FsReadOnly`` on a read only mount."""
        if self.readonly:
            raise FsReadOnly(f"the fs mount {self.root!r} is read only")

    # --- queries ------------------------------------------------------------

    def where(self, p: object = ".") -> str:
        """The absolute path of ``p``, checked, for handing to code outside Nu."""
        return self.resolve(p)

    def stat(self, p: object) -> dict[str, object] | None:
        """``p``'s entry, the link itself for a link; None when nothing is there."""
        full = self.resolve(p, leaf=False)
        try:
            info = os.lstat(full)
        except (FileNotFoundError, NotADirectoryError):
            return None
        return entry(self.relative(full), info)

    def has(self, p: object, kind: str | None = None) -> bool:
        """Whether something sits at ``p``; of the given kind, ``"file"`` or ``"dir"``."""
        if kind not in (None, "file", "dir"):
            raise ValueError(f"has() kind is None, 'file' or 'dir', got {kind!r}")
        full = self.resolve(p)
        if kind == "file":
            return Path(full).is_file()
        if kind == "dir":
            return Path(full).is_dir()
        return Path(full).exists()

    def usage(self) -> dict[str, int]:
        """The mount's file system in bytes: ``{total, free, used}``."""
        total, used, free = shutil.disk_usage(self.root)
        return {"total": total, "free": free, "used": used}

    def read_text(self, p: object, encoding: str = "utf-8") -> str:
        """The file's text, whole."""
        with Path(self.resolve(p)).open(encoding=encoding) as f:
            return f.read()

    def read_bytes(self, p: object, start: int = 0, end: int | None = None) -> bytes:
        """The file's bytes in ``[start, end)``, clamped to its size."""
        check_range(start, end)
        with Path(self.resolve(p)).open("rb") as f:
            size = os.fstat(f.fileno()).st_size
            lo, hi = clamp(start, end, size)
            f.seek(lo)
            return f.read(hi - lo)

    def listing(
        self,
        p: object = ".",
        pattern: str = "*",
        recursive: bool = False,
        kind: str | None = None,
    ) -> Iterator[dict[str, object]]:
        """The entries under the dir ``p``, a lazy walk; the dir is checked now."""
        if kind is not None and kind not in KINDS:
            raise ValueError(f"list() kind is None or one of {sorted(KINDS)}, got {kind!r}")
        full = self.resolve(p)
        if not Path(full).is_dir():
            if os.path.lexists(full):
                raise NotADirectoryError(f"{_shown(p)} is not a directory")
            raise FileNotFoundError(f"no directory at {_shown(p)}")
        return self._walk(full, pattern, recursive=recursive, kind=kind)

    def _walk(
        self, top: str, pattern: str, *, recursive: bool, kind: str | None
    ) -> Iterator[dict[str, object]]:
        """Each entry under ``top``, names sorted per dir, links never descended."""
        with os.scandir(top) as it:
            found = sorted(it, key=lambda e: e.name)
        for item in found:
            info = item.stat(follow_symlinks=False)
            row = entry(self.relative(item.path), info)
            if fnmatch.fnmatchcase(item.name, pattern) and (kind is None or row["kind"] == kind):
                yield row
            if recursive and row["kind"] == "dir":
                yield from self._walk(item.path, pattern, recursive=True, kind=kind)

    def pieces(
        self, p: object, start: int = 0, end: int | None = None, step: int = STEP
    ) -> Iterator[bytes]:
        """The file's bytes in ``[start, end)`` as pieces of ``step``; the path is checked now."""
        check_range(start, end)
        if step <= 0:
            raise ValueError(f"step must be positive, got {step}")
        return _pieces(self.resolve(p), start, end, step)

    def lines(self, p: object, encoding: str = "utf-8") -> Iterator[str]:
        """The file's lines without their newline; the path is checked now."""
        return _lines(self.resolve(p), encoding)

    def digest(self, p: object, algo: str = "sha256") -> str:
        """The hex digest of the file's bytes, read a piece at a time."""
        h = hashlib.new(algo)
        for piece in _pieces(self.resolve(p), 0, None, STEP):
            h.update(piece)
        return h.hexdigest()


# --- helpers ----------------------------------------------------------------


def check_follow(follow: object) -> None:
    """Refuse a ``follow`` rule that is not one of ``FOLLOW``."""
    if follow not in FOLLOW:
        raise ValueError(f"follow is 'inside', 'never' or 'any', got {follow!r}")


def split(p: object) -> tuple[str, ...]:
    """``p``'s parts, ``.`` dropped and ``..`` applied, refusing any that leave the mount."""
    if isinstance(p, PurePath):
        if p.is_absolute() or p.anchor:
            raise FsEscape(f"{_shown(p)} is absolute; fs paths are relative to the mount")
        text = p.as_posix()
    elif isinstance(p, str):
        text = p
    else:
        raise TypeError(f"an fs path is a str or a PurePath, got {type(p).__name__}")
    if "\x00" in text:
        raise ValueError(f"{_shown(p)} holds a NUL byte")
    if text.startswith("/"):
        raise FsEscape(f"{_shown(p)} is absolute; fs paths are relative to the mount")
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise FsEscape(f"{_shown(p)} climbs out of the mount")
            parts.pop()
            continue
        parts.append(part)
    return tuple(parts)


def entry(path: PurePosixPath, info: os.stat_result) -> dict[str, object]:
    """One entry's dict: ``{path, name, kind, size, mtime, mode}``."""
    return {
        "path": path,
        "name": path.name,
        "kind": kind_of(info.st_mode),
        "size": info.st_size,
        "mtime": info.st_mtime,
        "mode": st.S_IMODE(info.st_mode),
    }


def kind_of(mode: int) -> str:
    """``"file"``, ``"dir"``, ``"link"`` or ``"other"`` for an lstat mode."""
    if st.S_ISLNK(mode):
        return "link"
    if st.S_ISDIR(mode):
        return "dir"
    if st.S_ISREG(mode):
        return "file"
    return "other"


def check_range(start: object, end: object) -> None:
    """Refuse a range bound that is no ``int`` or is negative."""
    for name, bound in (("start", start), ("end", end)):
        if bound is None and name == "end":
            continue
        if not isinstance(bound, int) or isinstance(bound, bool):
            raise TypeError(f"{name} is an int, got {bound!r}")
        if bound < 0:
            raise ValueError(f"{name} must not be negative, got {bound}")


def clamp(start: int, end: int | None, size: int) -> tuple[int, int]:
    """The half-open range cut to ``[0, size)``; an inverted one comes back empty."""
    start = min(start, size)
    end = size if end is None else min(end, size)
    return start, max(start, end)


def _pieces(full: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
    with Path(full).open("rb") as f:
        size = os.fstat(f.fileno()).st_size
        lo, hi = clamp(start, end, size)
        f.seek(lo)
        left = hi - lo
        while left > 0:
            piece = f.read(min(step, left))
            if not piece:
                return
            left -= len(piece)
            yield piece


def _lines(full: str, encoding: str) -> Iterator[str]:
    with Path(full).open(encoding=encoding) as f:
        for line in f:
            yield line[:-1] if line.endswith("\n") else line


def _shown(p: object) -> str:
    """``p`` as an error message names it."""
    return repr(p.as_posix() if isinstance(p, PurePath) else p)
