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

Locks are ``fcntl.lockf`` record locks, never ``flock``, so NFS carries them
across machines. A POSIX lock belongs to the process and any descriptor on
the file, closed, drops it, so the locks this process holds sit in ``HELD``
and every lock op here checks it before opening the file.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import fcntl
import fnmatch
import hashlib
import json
import os
import secrets
import shutil
import socket
import stat as st
import tempfile
import threading
import time
import warnings
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING

from nu.context import Fabric

from .errors import FsEscape, FsLocked, FsLockWarning, FsReadOnly


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang.runtime import Context


__all__ = ["FOLLOW", "HELD", "KINDS", "STEP", "FsFabric", "Part"]


#: Bytes per piece a stream reads, unless told otherwise.
STEP = 1 << 20

#: The ``follow`` rules a mount takes.
FOLLOW = frozenset({"inside", "never", "any"})

#: What an entry's ``kind`` can be.
KINDS = frozenset({"file", "dir", "link", "other"})

#: The lock files this process holds, by absolute path, each with its holder
#: record. A POSIX lock is the process's, and closing any descriptor on the
#: file drops it, so code here that would open one of these checks this first.
HELD: dict[str, dict[str, object]] = {}

#: Guards ``HELD`` between the threads of one process taking locks at once.
_HELD_GUARD = threading.Lock()

#: ``lockf`` errnos meaning another process holds the lock.
TAKEN = frozenset({errno.EACCES, errno.EAGAIN})

#: ``lockf`` errnos meaning the file system cannot lock at all.
NO_LOCKS = frozenset({errno.ENOLCK, errno.EOPNOTSUPP, errno.ENOTSUP, errno.EINVAL})


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

    # --- writes -------------------------------------------------------------

    def write(
        self, p: object, data: object, *, exclusive: bool = False, mode: int | None = None
    ) -> None:
        """Write ``data`` to the file whole: a temp in the same dir, fsynced, then moved in.

        A reader sees the old bytes or the new ones, never half. Exclusive,
        the temp is linked in, so a taken name raises ``FileExistsError`` and
        is left as it was.
        """
        self.writable()
        buf = as_bytes(data)
        full = self._target(p)
        if exclusive and os.path.lexists(full):
            raise FileExistsError(f"{_shown(p)} is taken")
        fd, temp = _temp(full)
        try:
            try:
                _write_all(fd, buf)
                _settle(fd, full, mode)
            finally:
                os.close(fd)
        except BaseException:
            Path(temp).unlink(missing_ok=True)
            raise
        _commit(temp, full, exclusive=exclusive, shown=_shown(p))

    def open_part(self, p: object, *, exclusive: bool = False, mode: int | None = None) -> Part:
        """A ``Part`` filling ``p.part`` beside ``p``, moved in place on ``commit``."""
        self.writable()
        full = self._target(p)
        if exclusive and os.path.lexists(full):
            raise FileExistsError(f"{_shown(p)} is taken")
        part = full + ".part"
        fd = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
        return Part(fd, part, full, exclusive=exclusive, mode=mode, shown=_shown(p))

    def append(self, p: object, data: object) -> None:
        """Add ``data`` to the end of the file, made when missing, in one ``O_APPEND`` write."""
        self.writable()
        buf = as_bytes(data)
        fd = self.open_append(p)
        try:
            _write_all(fd, buf)
        finally:
            os.close(fd)

    def open_append(self, p: object) -> int:
        """An ``O_APPEND`` descriptor on the file, made with its parents when missing."""
        self.writable()
        full = self._target(p)
        return os.open(full, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o666)

    def mkdir(self, *ps: object, mode: int | None = None) -> None:
        """Make each dir with its parents; one already there is left as it is."""
        self.writable()
        for p in ps:
            full = Path(self.resolve(p))
            if mode is None:
                full.mkdir(parents=True, exist_ok=True)
            else:
                full.mkdir(mode=mode, parents=True, exist_ok=True)

    def remove(self, *ps: object, tree: bool = False) -> None:
        """Remove each path; a missing one is a no-op, a dir needs ``tree`` unless empty."""
        self.writable()
        for p in ps:
            full = self._entry_path(p, "remove")
            try:
                info = os.lstat(full)
            except (FileNotFoundError, NotADirectoryError):
                continue
            if not st.S_ISDIR(info.st_mode):
                Path(full).unlink(missing_ok=True)
            elif tree:
                shutil.rmtree(full)
            else:
                Path(full).rmdir()

    def remove_if_holds(self, p: object, text: str) -> None:
        """Remove the file only while it holds exactly ``text``, the check under its lock.

        A missing file is a no-op. When a process, this one included, holds
        the file's lock the file is live and is left alone.
        """
        self.writable()
        want = as_bytes(text)
        if not split(p):
            raise PermissionError("refusing to remove the mount itself")
        # The file is opened and read, so its last part is checked too.
        full = self.resolve(p)
        with _HELD_GUARD:
            if full in HELD:
                return
            try:
                fd = os.open(full, os.O_RDWR)
            except (FileNotFoundError, NotADirectoryError):
                return
            try:
                try:
                    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    if exc.errno in TAKEN:
                        return
                    if exc.errno not in NO_LOCKS:
                        raise
                # Read through the locked descriptor: a second one, closed,
                # would drop the lock.
                if _read_fd(fd) == bytes(want):
                    Path(full).unlink(missing_ok=True)
            finally:
                os.close(fd)

    def move(self, src: object, dst: object, *, overwrite: bool = False) -> None:
        """Move ``src`` to ``dst``; a ``dst`` ending in ``/`` means into that dir.

        Without ``overwrite`` a taken ``dst`` raises ``FileExistsError``. Across
        devices the entry is copied, then the source removed.
        """
        self.writable()
        source = self._entry_path(src, "move")
        if not os.path.lexists(source):
            raise FileNotFoundError(f"nothing at {_shown(src)} to move")
        target = self._destination(src, dst)
        if overwrite:
            try:
                Path(source).replace(target)
            except OSError as exc:
                if exc.errno != errno.EXDEV:
                    raise
                _move_across(source, target)
            return
        if os.path.lexists(target):
            raise FileExistsError(f"{_shown(dst)} is taken")
        if not Path(source).is_dir() or Path(source).is_symlink():
            try:
                os.link(source, target, follow_symlinks=False)
            except FileExistsError:
                raise FileExistsError(f"{_shown(dst)} is taken") from None
            except OSError:
                pass  # no hard links here: the check above is the guard
            else:
                Path(source).unlink()
                return
        try:
            Path(source).rename(target)
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            _move_across(source, target)

    def copy(
        self, src: object, dst: object, *, overwrite: bool = False, verify: bool = False
    ) -> None:
        """Copy the file ``src`` to ``dst``, data and metadata, through a temp moved in whole.

        A ``dst`` ending in ``/`` means into that dir. ``verify`` compares the
        sha256 of the two before the copy is moved in.
        """
        self.writable()
        source = self.resolve(src)
        if Path(source).is_dir():
            raise IsADirectoryError(f"{_shown(src)} is a directory; copy copies files")
        target = self._destination(src, dst)
        if not overwrite and os.path.lexists(target):
            raise FileExistsError(f"{_shown(dst)} is taken")
        fd, temp = _temp(target)
        os.close(fd)
        try:
            shutil.copy2(source, temp)
            if verify and _sha256(source) != _sha256(temp):
                raise OSError(errno.EIO, f"copy of {_shown(src)} does not match its source")
        except BaseException:
            Path(temp).unlink(missing_ok=True)
            raise
        _commit(temp, target, exclusive=not overwrite, shown=_shown(dst))

    def touch(self, p: object) -> None:
        """Make the file when missing, with its parents, and set its mtime to now."""
        self.writable()
        Path(self._target(p)).touch()

    def make_temp(self, prefix: str = "tmp-", where: object = ".") -> PurePosixPath:
        """Make a fresh dir under ``where`` and give its path in the mount."""
        self.writable()
        base = Path(self.resolve(where))
        base.mkdir(parents=True, exist_ok=True)
        return self.relative(tempfile.mkdtemp(prefix=prefix, dir=base))

    # --- locks --------------------------------------------------------------

    def held(self, p: object) -> dict[str, object] | None:
        """The holder record of the lock on ``p``, or None when nobody holds it. Takes nothing.

        A lock this process holds is answered from ``HELD``. Any other is
        probed with a shared ``lockf`` on a read only descriptor, which
        conflicts only with a holder's exclusive one; a holder that left no
        record reads as ``{}``.
        """
        full = self.resolve(p)
        # Under the guard: a lock taken in another thread between the look
        # at HELD and the close of the probe would be dropped by the close.
        with _HELD_GUARD:
            if full in HELD:
                return dict(HELD[full])
            try:
                fd = os.open(full, os.O_RDONLY)
            except (FileNotFoundError, NotADirectoryError):
                return None
            try:
                try:
                    fcntl.lockf(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                except OSError as exc:
                    if exc.errno in TAKEN:
                        return record_of(_read_fd(fd))
                    if exc.errno in NO_LOCKS:
                        return None
                    raise
                fcntl.lockf(fd, fcntl.LOCK_UN)
                return None
            finally:
                os.close(fd)

    def lock(self, p: object, what: str = "") -> tuple[str, int | None]:
        """Take the exclusive lock on ``p`` without waiting, and write who holds it.

        Returns:
            ``(full, fd)``, for ``unlock``. ``fd`` is None when the file
            system cannot lock: a ``FsLockWarning`` is raised as a warning
            and nothing is held.

        Raises:
            FsLocked: another process, or this one, holds it.
        """
        self.writable()
        full = self._target(p)
        with _HELD_GUARD:
            if full in HELD:
                record = dict(HELD[full])
                raise FsLocked(told(_shown(p), record) + " (this process)", record)
            fd = os.open(full, os.O_RDWR | os.O_CREAT, 0o644)
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in TAKEN:
                    record = record_of(_read_fd(fd))
                    os.close(fd)
                    raise FsLocked(told(_shown(p), record), record) from None
                os.close(fd)
                if exc.errno not in NO_LOCKS:
                    raise
                warnings.warn(
                    f"could not lock {_shown(p)} ({exc}); going on without the lock",
                    FsLockWarning,
                    stacklevel=2,
                )
                return full, None
            record: dict[str, object] = {
                "host": socket.gethostname(),
                "pid": os.getpid(),
                "what": what,
                "taken_at": time.time(),
            }
            try:
                os.ftruncate(fd, 0)
                _write_all(fd, (json.dumps(record) + "\n").encode("utf-8"))
            except BaseException:
                with contextlib.suppress(OSError):
                    fcntl.lockf(fd, fcntl.LOCK_UN)
                os.close(fd)
                raise
            HELD[full] = record
        return full, fd

    @staticmethod
    def unlock(full: str, fd: int | None) -> None:
        """Release a lock ``lock`` took. The file stays, naming its last holder."""
        if fd is None:
            return
        with _HELD_GUARD:
            HELD.pop(full, None)
            with contextlib.suppress(OSError):
                fcntl.lockf(fd, fcntl.LOCK_UN)
            os.close(fd)

    # --- write helpers ------------------------------------------------------

    def _target(self, p: object) -> str:
        """The file ``p`` names, checked, its parents made; a dir there is refused."""
        full = self.resolve(p)
        if not split(p):
            raise IsADirectoryError("the mount itself is a directory, not a file")
        if Path(full).is_dir():
            raise IsADirectoryError(f"{_shown(p)} is a directory")
        Path(full).parent.mkdir(parents=True, exist_ok=True)
        return full

    def _entry_path(self, p: object, verb: str) -> str:
        """The entry ``p`` names, its last part unfollowed; the mount itself is refused."""
        if not split(p):
            raise PermissionError(f"refusing to {verb} the mount itself")
        return self.resolve(p, leaf=False)

    def _destination(self, src: object, dst: object) -> str:
        """Where ``dst`` puts ``src``: into the dir for a trailing ``/``, parents made."""
        into = isinstance(dst, str) and dst.endswith("/")
        if into:
            folder = Path(self.resolve(dst))
            folder.mkdir(parents=True, exist_ok=True)
            name = split(src)[-1:] or ("",)
            target = str(folder / name[0])
            self.resolve(self.relative(target), leaf=False)
            return target
        if not split(dst):
            raise IsADirectoryError(
                "the mount itself is a directory; end dst with '/' to move into it"
            )
        target = self.resolve(dst, leaf=False)
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        return target


class Part:
    """A file filling at ``<p>.part``, moved over ``p`` whole when the stream is drained.

    Plain sync methods; an async run calls each in a thread.
    """

    def __init__(
        self, fd: int, part: str, full: str, *, exclusive: bool, mode: int | None, shown: str
    ) -> None:
        self.fd = fd
        self.part = part
        self.full = full
        self.exclusive = exclusive
        self.mode = mode
        self.shown = shown

    def write(self, piece: object) -> None:
        """Add one piece."""
        _write_all(self.fd, as_bytes(piece))

    def commit(self) -> None:
        """Fsync, close and move the part in place."""
        try:
            _settle(self.fd, self.full, self.mode)
        except BaseException:
            self.abort()
            raise
        os.close(self.fd)
        if self.exclusive:
            try:
                os.link(self.part, self.full)
            except FileExistsError:
                raise FileExistsError(f"{self.shown} is taken") from None
            finally:
                Path(self.part).unlink(missing_ok=True)
        else:
            Path(self.part).replace(self.full)

    def abort(self) -> None:
        """Close and remove the part, leaving ``p`` as it was."""
        with contextlib.suppress(OSError):
            os.close(self.fd)
        Path(self.part).unlink(missing_ok=True)


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


def as_bytes(data: object) -> bytes | memoryview:
    """``data`` as bytes to write: ``bytes``-like as given, ``str`` as UTF-8."""
    if isinstance(data, str):
        return data.encode("utf-8")
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, memoryview):
        return data
    raise TypeError(f"fs writes take str or bytes, got {type(data).__name__}")


def _temp(full: str) -> tuple[int, str]:
    """A fresh temp file beside ``full``, ``.<name>.<token>.tmp``, open for writing."""
    head, name = os.path.split(full)
    while True:
        temp = os.path.join(head, f".{name}.{secrets.token_hex(6)}.tmp")  # noqa: PTH118 - str paths
        try:
            return os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666), temp
        except FileExistsError:
            continue


def _write_all(fd: int, data: bytes | memoryview) -> None:
    view = memoryview(data)
    while view:
        done = os.write(fd, view)
        view = view[done:]


def _settle(fd: int, full: str, mode: int | None) -> None:
    """Set the new file's mode (given, else the one it replaces) and fsync it."""
    if mode is None:
        with contextlib.suppress(OSError):
            mode = st.S_IMODE(Path(full).stat().st_mode)
    if mode is not None:
        os.fchmod(fd, mode)
    os.fsync(fd)


def _commit(temp: str, full: str, *, exclusive: bool, shown: str) -> None:
    """Move ``temp`` over ``full``: replace, or link so a taken name refuses."""
    try:
        if exclusive:
            try:
                os.link(temp, full)
            except FileExistsError:
                raise FileExistsError(f"{shown} is taken") from None
        else:
            Path(temp).replace(full)
    finally:
        Path(temp).unlink(missing_ok=True)


def _read_fd(fd: int) -> bytes:
    """All of an open file's bytes, read from its start without moving the offset."""
    size = os.fstat(fd).st_size
    out = bytearray()
    while len(out) < size:
        piece = os.pread(fd, size - len(out), len(out))
        if not piece:
            break
        out += piece
    return bytes(out)


def record_of(raw: bytes) -> dict[str, object]:
    """A lock file's holder record, ``{host, pid, what, taken_at}``; ``{}`` when it says nothing."""
    try:
        found = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {}
    return found if isinstance(found, dict) else {}


def told(shown: str, record: dict[str, object]) -> str:
    """A refusal naming the holder: ``'a.lock' is locked for 'indexer' on red, pid 1234``."""
    what = record.get("what")
    guarding = f" for {what!r}" if what else ""
    if "pid" not in record:
        return f"{shown} is locked{guarding} by a process that left no record"
    return f"{shown} is locked{guarding} on {record.get('host')}, pid {record.get('pid')}"


def _sha256(full: str) -> str:
    h = hashlib.sha256()
    for piece in _pieces(full, 0, None, STEP):
        h.update(piece)
    return h.hexdigest()


def _move_across(source: str, target: str) -> None:
    """Move to another device: copy the entry, then remove the source."""
    if Path(source).is_dir() and not Path(source).is_symlink():
        shutil.copytree(source, target, symlinks=True)
        shutil.rmtree(source)
    else:
        shutil.copy2(source, target, follow_symlinks=False)
        Path(source).unlink()


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
