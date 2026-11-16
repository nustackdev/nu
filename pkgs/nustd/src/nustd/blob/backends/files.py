"""Blobs as plain files in a directory tree, one file per id."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from .._base import LocalBackend, check_id, check_range, clamp
from ..protocol import STEP, BlobExists, BlobInfo, BlobNotFound


if TYPE_CHECKING:
    from collections.abc import Iterator

    from .._base import Staged


__all__ = ["FilesBackend"]


class FilesBackend(LocalBackend):
    """Blobs as files: ``root/blobs/<id[:2]>/<id>`` with a ``<id>.json`` meta beside it.

    A put fills a temp file in ``root/tmp`` and ``os.link``s it into place.
    The link fails when the id is taken, so write-once comes from the
    filesystem itself, across processes, with no lock. The meta is written
    last and deleted first: a blob exists exactly while its meta does.

    Limits:

    - Size is whatever the disk holds.
    - ``root/tmp`` must sit on the same filesystem as ``root/blobs`` (it does,
      unless one of them is a mount point), or the link fails.
    - A path source is copied, never linked: a link would let later edits to
      the caller's file change a write-once blob.
    - Data and meta are fsynced, their directories are not: a machine crash
      right after a put can lose it, never tear it.
    - A put that dies between the link and the meta leaves the data with no
      meta: invisible, but its id is taken until ``delete`` clears it.
      Spool files of a process that died mid-put stay in ``root/tmp``.
    - A stream that has begun keeps reading a blob deleted under it (POSIX
      keeps an open file); one that has not begun gets ``BlobNotFound``.
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)

    def open(self) -> None:
        """Create the tree on first use."""
        (self.root / "blobs").mkdir(parents=True, exist_ok=True)
        self._spool_dir.mkdir(exist_ok=True)

    def close(self) -> None:
        """Nothing to release: every call opens and closes its own files."""

    @property
    def _spool_dir(self) -> Path:
        return self.root / "tmp"

    def _data_path(self, blob_id: str) -> Path:
        return self.root / "blobs" / blob_id[:2] / blob_id

    def _meta_path(self, blob_id: str) -> Path:
        return self.root / "blobs" / blob_id[:2] / f"{blob_id}.json"

    def _temp(self) -> tuple[int, Path]:
        fd, name = tempfile.mkstemp(dir=self._spool_dir, prefix="put-")
        return fd, Path(name)

    def _stage_file(self, staged: Staged) -> Path:
        """A temp file of ours holding the bytes, fsynced, ready to link."""
        if staged.owned:
            assert staged.path is not None  # noqa: S101 (an owned Staged is a path)
            _fsync(staged.path)
            return staged.path
        fd, temp = self._temp()
        try:
            with os.fdopen(fd, "wb") as out:
                if staged.buffer is not None:
                    out.write(staged.buffer)
            if staged.path is not None:
                # copyfile hands the copy to the kernel (sendfile) where it can.
                shutil.copyfile(staged.path, temp)
            _fsync(temp)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
        return temp

    def _store(self, blob_id: str, staged: Staged, mime: str, name: str) -> BlobInfo:
        temp = self._stage_file(staged)
        try:
            info = BlobInfo(
                id=blob_id,
                size=temp.stat().st_size,
                mime=mime,
                name=name,
                created_at=time.time(),
            )
            data = self._data_path(blob_id)
            data.parent.mkdir(exist_ok=True)
            try:
                os.link(temp, data)
            except FileExistsError:
                raise BlobExists(blob_id) from None
            try:
                self._write_meta(info)
            except BaseException:
                data.unlink(missing_ok=True)
                raise
        finally:
            if not staged.owned:
                temp.unlink(missing_ok=True)
        return info

    def _write_meta(self, info: BlobInfo) -> None:
        fd, temp = self._temp()
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                json.dump(info.to_dict(), out)
                out.flush()
                os.fsync(out.fileno())
            temp.replace(self._meta_path(info.id))
        except BaseException:
            temp.unlink(missing_ok=True)
            raise

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes."""
        check_id(blob_id)
        try:
            raw = self._meta_path(blob_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None
        return BlobInfo.from_dict(json.loads(raw))

    def exists(self, blob_id: str) -> bool:
        """Whether a whole blob sits under the id: its meta is there."""
        check_id(blob_id)
        return self._meta_path(blob_id).exists()

    def _open_data(self, blob_id: str) -> Path:
        if not self._meta_path(blob_id).exists():
            raise BlobNotFound(blob_id)
        return self._data_path(blob_id)

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, in one piece."""
        check_id(blob_id)
        check_range(start, end)
        try:
            with self._open_data(blob_id).open("rb") as file:
                lo, hi = clamp(start, end, os.fstat(file.fileno()).st_size)
                file.seek(lo)
                return file.read(hi - lo)
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None

    def stream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
    ) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time, from one open file."""
        check_id(blob_id)
        check_range(start, end, step)
        return self._pieces(blob_id, start, end, step)

    def _pieces(self, blob_id: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
        try:
            file = self._open_data(blob_id).open("rb")
        except FileNotFoundError:
            raise BlobNotFound(blob_id) from None
        with file:
            pos, stop = clamp(start, end, os.fstat(file.fileno()).st_size)
            file.seek(pos)
            while pos < stop:
                piece = file.read(min(step, stop - pos))
                if not piece:
                    return
                yield piece
                pos += len(piece)

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one.

        Also clears data a dead put left behind with no meta.
        """
        check_id(blob_id)
        try:
            self._meta_path(blob_id).unlink()
            found = True
        except FileNotFoundError:
            found = False
        self._data_path(blob_id).unlink(missing_ok=True)
        return found


def _fsync(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
