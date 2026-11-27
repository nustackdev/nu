"""Blobs as plain files in a directory tree, one file per id."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .._base import Busy, LocalBackend, _as_buffer, _pieces, _too_large, check_id, clamp
from ..protocol import BlobExists, BlobInfo, BlobNotFound, BlobSealed


if TYPE_CHECKING:
    from collections.abc import Iterator


__all__ = ["DEFAULT_BATCH_SIZE", "FilesBackend"]


DEFAULT_BATCH_SIZE = 8 << 20
"""8 MiB written between two commits of a put or an append.

A commit fsyncs the data and rewrites the meta: a follower sees a streamed
put grow 8 MiB at a time.
"""

_WRITE_MAX = 1 << 30
"""The most bytes one ``write`` call is handed: macOS refuses one past ``INT_MAX``."""

_HOLD = 1 << 20
"""Bytes of an async source held on the event loop before a thread writes them.

Fewer when the batch fills first, so a follower sees each batch commit.
"""

_WRITING = "writing"
"""The meta key a put's commits carry until its last one: a put still under way."""


class FilesBackend(LocalBackend):
    """Blobs as files: ``root/blobs/<id[:2]>/<id>`` with a ``<id>.json`` meta beside it.

    A put creates the data file under its final name (``O_EXCL``: the create
    fails when the id is taken, so write-once comes from the filesystem
    itself, across processes) and appends to it in place. Every
    ``batch_size`` bytes, and when the source ends, it commits: the data is
    fsynced and the meta, with the size committed so far, is rewritten
    atomically (temp file and rename). A reader reads the data only up to
    the meta's size, so a blob is readable from its first commit and never
    shows bytes that are not committed. A blob exists exactly while its meta
    does; the meta is written last and deleted first.

    One writer per blob: a put or an append holds an exclusive ``flock`` on
    the data file while it runs, and a second append, or a seal, waits for
    it. The lock goes with the process, so a writer that dies frees the blob.
    A put's commits carry a mark in the meta until its last one; a reader
    that finds the mark and no lock held knows the put died, and reads the
    blob as missing. An append that fails is cut back to its last commit.

    Limits:

    - Size is whatever the disk holds.
    - A path source is copied, never linked: a link would let later edits to
      the caller's file change a blob.
    - Data and meta are fsynced, their directories are not: a machine crash
      right after a commit can lose it, never tear it.
    - A put that dies leaves its data, and its meta when it committed:
      invisible, but its id is taken until ``delete`` clears it.
    - An append that dies mid-way leaves bytes past the committed size in
      the data file, never read; the next append or the seal cuts them off.
    - The locks are ``flock``. On NFS, Linux emulates them with ``fcntl``
      locks, which never conflict within one process: there the one-writer
      rule holds across machines and processes, not between threads.
    - A stream that has begun keeps reading a blob deleted under it (POSIX
      keeps an open file); one that has not begun gets ``BlobNotFound``.

    Args:
        root: the tree's root, made on first open.
        batch_size: bytes written between two commits of a put or an append.
    """

    def __init__(
        self, root: str | os.PathLike[str], *, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> None:
        if batch_size < 1:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        self.root = Path(root)
        self.batch_size = batch_size

    def open(self) -> None:
        """Create the tree on first use."""
        (self.root / "blobs").mkdir(parents=True, exist_ok=True)
        self._temp_dir.mkdir(exist_ok=True)

    def close(self) -> None:
        """Nothing to release: every call opens and closes its own files."""

    @property
    def _temp_dir(self) -> Path:
        """Where a meta is written before it is renamed into place."""
        return self.root / "tmp"

    def _data_path(self, blob_id: str) -> Path:
        return self.root / "blobs" / blob_id[:2] / blob_id

    def _meta_path(self, blob_id: str) -> Path:
        return self.root / "blobs" / blob_id[:2] / f"{blob_id}.json"

    # ---- meta --------------------------------------------------------------------------------

    def _write_meta(self, info: BlobInfo, *, writing: bool = False) -> None:
        fd, name = tempfile.mkstemp(dir=self._temp_dir, prefix="meta-")
        temp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                record = info.to_dict()
                if writing:
                    record[_WRITING] = True
                json.dump(record, out)
                out.flush()
                os.fsync(out.fileno())
            temp.replace(self._meta_path(info.id))
        except BaseException:
            temp.unlink(missing_ok=True)
            raise

    def _record(self, blob_id: str) -> dict[str, Any]:
        try:
            raw = self._meta_path(blob_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None
        record: dict[str, Any] = json.loads(raw)
        return record

    def _put_died(self, blob_id: str) -> bool:
        """Whether the put a meta marks as under way is gone: no lock is held on its data."""
        try:
            fd = os.open(self._data_path(blob_id), os.O_RDONLY)
        except FileNotFoundError:
            return True
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return False  # its writer holds the lock
            try:
                # The put may have ended between the meta read and the lock.
                return bool(self._record(blob_id).get(_WRITING))
            except BlobNotFound:
                return True
        finally:
            os.close(fd)

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes."""
        check_id(blob_id)
        record = self._record(blob_id)
        if record.get(_WRITING) and self._put_died(blob_id):
            raise BlobNotFound(blob_id)
        return BlobInfo.from_dict(record)

    def exists(self, blob_id: str) -> bool:
        """Whether a blob sits under the id, open or sealed: its meta is there."""
        try:
            self.info(blob_id)
        except BlobNotFound:
            return False
        return True

    # ---- writes ------------------------------------------------------------------------------

    def _create(self, blob_id: str, mime: str, name: str, seal: bool) -> _FileWriter:
        """Create the data file under its final name and lock it; ``BlobExists`` when it is there."""
        data = self._data_path(blob_id)
        data.parent.mkdir(exist_ok=True)
        try:
            fd = os.open(data, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise BlobExists(blob_id) from None
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
        except BaseException:
            os.close(fd)
            data.unlink(missing_ok=True)
            raise
        info = BlobInfo(
            id=blob_id, size=0, mime=mime, name=name, created_at=time.time(), sealed=False
        )
        return _FileWriter(self, fd, info, seal=seal, putting=True)

    def _locked(self, blob_id: str) -> tuple[int, BlobInfo]:
        """The data file, opened and locked; its blob's info, read under the lock.

        ``Busy`` while another writer holds it, ``BlobNotFound`` when there is
        no blob or its put died.
        """
        try:
            fd = os.open(self._data_path(blob_id), os.O_WRONLY)
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy(blob_id) from None
            record = self._record(blob_id)
            if record.get(_WRITING):
                raise BlobNotFound(blob_id)  # the lock was free: its put died
        except BaseException:
            os.close(fd)
            raise
        return fd, BlobInfo.from_dict(record)

    def _begin_append(self, blob_id: str) -> _FileWriter:
        """Lock the open blob's data file and cut it back to the committed size."""
        fd, info = self._locked(blob_id)
        try:
            if info.sealed:
                raise BlobSealed(blob_id)
            os.ftruncate(fd, info.size)
            os.lseek(fd, info.size, os.SEEK_SET)
        except BaseException:
            os.close(fd)
            raise
        return _FileWriter(self, fd, info, seal=False, putting=False)

    def _seal_once(self, blob_id: str) -> BlobInfo:
        """Lock the data file, cut it back to the committed size and mark the meta sealed."""
        info = self.info(blob_id)
        if info.sealed:
            return info
        fd, info = self._locked(blob_id)
        try:
            if info.sealed:
                return info
            os.ftruncate(fd, info.size)
            os.fsync(fd)
            info = replace(info, sealed=True)
            self._write_meta(info)
            return info
        finally:
            os.close(fd)

    # ---- reads -------------------------------------------------------------------------------

    def _read(self, blob_id: str, start: int, end: int | None) -> bytes | None:
        """The bytes of a range, in one piece, up to the committed size."""
        info = self.info(blob_id)
        if not info.sealed and (end is None or end > info.size):
            return None
        try:
            with self._data_path(blob_id).open("rb") as file:
                lo, hi = clamp(start, end, info.size)
                file.seek(lo)
                return file.read(hi - lo)
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None

    def _pieces(self, blob_id: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
        info = self.info(blob_id)
        try:
            file = self._data_path(blob_id).open("rb")
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None
        with file:
            pos, stop = clamp(start, end, info.size)
            file.seek(pos)
            while pos < stop:
                piece = file.read(min(step, stop - pos))
                if not piece:
                    return
                yield piece
                pos += len(piece)

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one.

        An open blob goes too, while it is written: its writer's next commit
        raises ``BlobNotFound``. Also clears data a dead put left behind.
        """
        check_id(blob_id)
        found = self.exists(blob_id)
        self._meta_path(blob_id).unlink(missing_ok=True)
        self._data_path(blob_id).unlink(missing_ok=True)
        return found


class _FileWriter:
    """One put's or one append's trip into a data file: bytes appended in place, committed by a meta rewrite."""

    def __init__(
        self, backend: FilesBackend, fd: int, info: BlobInfo, *, seal: bool, putting: bool
    ) -> None:
        self._backend = backend
        self._fd = fd
        self._info = info
        self._seal = seal
        self._putting = putting
        self._size = self._committed = info.size
        self._held = bytearray()
        stat = os.fstat(fd)
        self._file = (stat.st_dev, stat.st_ino)

    def _count(self, size: int) -> None:
        error = _too_large(self._size + len(self._held) + size, self._backend.max_size)
        if error is not None:
            raise error

    def _write(self, view: memoryview) -> None:
        """Append to the data file, committing each time a batch fills."""
        batch = self._backend.batch_size
        while view.nbytes:
            room = batch - (self._size - self._committed)
            part = view[: min(room, _WRITE_MAX)]
            written = os.write(self._fd, part)
            self._size += written
            view = view[written:]
            if self._size - self._committed >= batch:
                self._commit(last=False)

    def _commit(self, *, last: bool) -> None:
        os.fsync(self._fd)
        self._check_ours()
        sealed = last and self._seal
        info = replace(self._info, size=self._size, sealed=sealed)
        self._backend._write_meta(info, writing=self._putting and not last)
        self._info = info
        self._committed = self._size

    def _check_ours(self) -> None:
        """Refuse to commit once the data file was deleted, or replaced, under this writer."""
        try:
            stat = self._backend._data_path(self._info.id).stat()
        except FileNotFoundError:
            raise BlobNotFound(self._info.id) from None
        if (stat.st_dev, stat.st_ino) != self._file:
            raise BlobNotFound(self._info.id)

    # ---- the Writer surface ------------------------------------------------------------------

    def take(self, source: object, kind: str) -> None:
        """Write a whole sync source in, committing as batches fill."""
        if kind == "buffer":
            view = _as_buffer(source)  # type: ignore[arg-type]
            self._count(view.nbytes)
            self._write(view)
        elif kind == "path":
            with Path(source).open("rb") as file:  # type: ignore[arg-type]
                for piece in _pieces(file):
                    self._take_piece(piece)
        else:
            for piece in _pieces(source):
                self._take_piece(piece)

    def _take_piece(self, piece: object) -> None:
        view = memoryview(piece).cast("B")  # type: ignore[arg-type]
        self._count(view.nbytes)
        self._write(view)

    def feed(self, piece: object) -> bool:
        """Hold the next piece; True once a thread should write what is held."""
        view = memoryview(piece).cast("B")  # type: ignore[arg-type]
        self._count(view.nbytes)
        self._held += view
        room = self._backend.batch_size - (self._size - self._committed)
        return len(self._held) >= min(_HOLD, room)

    def flush(self) -> None:
        """Write what ``feed`` holds."""
        held, self._held = self._held, bytearray()
        self._write(memoryview(held))

    def finish(self) -> BlobInfo:
        """Write the rest and commit, sealed or not as the call asked."""
        self.flush()
        self._commit(last=True)
        return self._info

    def fail(self) -> None:
        """A put deletes its blob, while the data file is still its own; an append cuts back to its last commit."""
        self._held = bytearray()
        if self._putting:
            try:
                self._check_ours()
            except BlobNotFound:
                return
            self._backend._meta_path(self._info.id).unlink(missing_ok=True)
            self._backend._data_path(self._info.id).unlink(missing_ok=True)
            return
        try:
            os.ftruncate(self._fd, self._committed)
        except OSError:
            pass  # cut off by the next append or the seal

    def close(self) -> None:
        """Close the data file, which drops the lock."""
        if self._fd >= 0:
            fd, self._fd = self._fd, -1
            os.close(fd)
