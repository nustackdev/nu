"""Blobs in one LMDB environment, each value whole under its id."""

from __future__ import annotations

import json
import mmap
import os
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .._base import LocalBackend, check_id, check_range, clamp
from ..protocol import STEP, BlobExists, BlobInfo, BlobNotFound, BlobTooLarge


if TYPE_CHECKING:
    from collections.abc import Iterator

    from .._base import Staged


__all__ = [
    "DEFAULT_MAP_SIZE",
    "DEFAULT_MAX_READERS",
    "DEFAULT_WRITEMAP",
    "MAX_VALUE",
    "MAX_WRITE",
    "LMDBBackend",
]


DEFAULT_MAP_SIZE = 1 << 40
"""1 TiB of address space.

The file is sparse, so the size costs nothing until used.
"""

DEFAULT_MAX_READERS = 1024
"""Reader slots shared by every process on the env.

Each short read txn takes one.
"""

DEFAULT_WRITEMAP = sys.platform != "darwin"
"""Writemap on Linux, off on macOS.

On macOS a writemap commit costs about 14 ms per GiB of ``map_size``, written
or not: a 200 KiB put into the 1 TiB default map takes 14 s there, 39 ms
without writemap. Linux has no such cost and keeps the RAM saving.
"""

MAX_VALUE = (1 << 32) - 1
"""LMDB keeps a value's size in 32 bits."""

MAX_WRITE = (1 << 31) - 1
"""The most one value holds here: macOS refuses one ``write`` past ``INT_MAX``.

Without writemap LMDB writes a value at commit in one call, so past this the
commit fails with ``EINVAL``. One cap on every platform keeps it simple.
"""


class LMDBBackend(LocalBackend):
    """Blobs in one LMDB environment: a value per id, ranges read straight from the map.

    Two named dbs, ``data`` (id to bytes) and ``meta`` (id to json), written
    in one transaction, so a blob shows up whole or not at all.

    Limits, all native to LMDB:

    - One value holds at most ``MAX_WRITE`` bytes (just under 2 GiB). A
      bigger put raises ``BlobTooLarge`` before anything is written.
    - No streamed put: py-lmdb has no ``MDB_RESERVE``, so a value goes in as
      one write. A path goes in from an mmap of itself; a file or an iterable
      spools to a temp file inside the env directory and goes in from an mmap
      of that, so neither ever sits whole in Python memory.
    - A put holds the env's single writer lock for its copy: puts from every
      process queue behind it. Readers never wait. Within one process, puts
      and deletes also pass through a ``threading.Lock`` first: py-lmdb hangs
      every thread when one write txn aborts while another thread waits to
      begin one, and a put that loses an id race aborts.
    - A path source is put from an mmap of the caller's file. It must not be
      truncated while its put runs: touching a mapped page past the new end
      kills the process with SIGBUS, not a Python exception.
    - The env must be on local disk, never NFS (mmap plus a lock file). LMDB
      allows one open env per path per process, so every instance on one path
      in a process shares one env and one write lock, counted: the last
      ``close`` closes it. An instance whose ``map_size``, ``max_readers`` or
      ``writemap`` differ from the env already open on its path raises
      ``ValueError`` at ``open``. Start children with ``spawn``: an env open
      across a ``fork`` is unsafe.
    - ``map_size`` is fixed while open: a full map raises ``lmdb.MapFullError``
      and growing it means reopening in every process.
    - With ``writemap`` (the default on Linux) a put copies straight into
      the map. Without it LMDB first builds the whole value in C heap pages,
      so a put costs its full size in RAM. The price of ``writemap``:
      ``data.mdb`` is sized to ``map_size`` up front. It stays sparse (only
      written pages take disk), but it reads as 1 TiB to ``ls`` and to copy
      tools that do not keep holes, and needs a filesystem with sparse files.
      On macOS it is off by default: there every writemap commit costs time
      in proportion to ``map_size`` (see ``DEFAULT_WRITEMAP``).
    - Spool files of a process that died mid-put stay in ``<path>/tmp``.
    - A stream opens a short read txn per piece and copies only that piece, so
      a slow consumer pins no pages and holds no reader slot between pulls.
      The price: a blob deleted mid-stream raises ``BlobNotFound`` at the next
      pull, and so does one deleted and put again under the same id.
    """

    max_size: int = MAX_WRITE

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        map_size: int = DEFAULT_MAP_SIZE,
        max_readers: int = DEFAULT_MAX_READERS,
        writemap: bool = DEFAULT_WRITEMAP,
    ) -> None:
        self.path = Path(path)
        self.map_size = map_size
        self.max_readers = max_readers
        self.writemap = writemap
        self._env: Any = None
        self._data: Any = None
        self._meta: Any = None
        self._write_lock: Any = None
        self._key: str | None = None

    def open(self) -> None:
        """Open the env, creating it and its two dbs on first use.

        Shares the env another instance in this process already holds open on
        the same path.
        """
        if self._env is not None:
            return
        self._spool_dir.mkdir(parents=True, exist_ok=True)
        key = os.path.realpath(self.path)
        with _SHARED_LOCK:
            shared = _SHARED.get(key)
            if shared is None:
                shared = self._open_env()
                _SHARED[key] = shared
            else:
                self._check_options(shared)
            shared.count += 1
        self._key = key
        self._env, self._data, self._meta = shared.env, shared.data, shared.meta
        self._write_lock = shared.write_lock

    def _open_env(self) -> _Shared:
        try:
            import lmdb
        except ImportError as error:
            raise ImportError("LMDBBackend needs lmdb: install nustd[blob]") from error
        env = lmdb.open(
            str(self.path),
            map_size=self.map_size,
            max_dbs=2,
            max_readers=self.max_readers,
            writemap=self.writemap,
            subdir=True,
        )
        try:
            data = env.open_db(b"data")
            meta = env.open_db(b"meta")
            env.reader_check()
        except BaseException:
            env.close()
            raise
        return _Shared(
            env=env,
            data=data,
            meta=meta,
            write_lock=threading.Lock(),
            map_size=self.map_size,
            max_readers=self.max_readers,
            writemap=self.writemap,
        )

    def _check_options(self, shared: _Shared) -> None:
        mine = (self.map_size, self.max_readers, self.writemap)
        theirs = (shared.map_size, shared.max_readers, shared.writemap)
        if mine != theirs:
            msg = (
                f"the LMDB env at {self.path} is already open in this process with "
                f"map_size, max_readers, writemap = {theirs}, not {mine}"
            )
            raise ValueError(msg)

    def close(self) -> None:
        """Let go of the env; the last instance on its path closes it."""
        if self._env is None:
            return
        key = self._key
        self._env = self._data = self._meta = self._write_lock = self._key = None
        with _SHARED_LOCK:
            shared = _SHARED[key]  # type: ignore[index]
            shared.count -= 1
            if shared.count == 0:
                del _SHARED[key]  # type: ignore[arg-type]
                shared.env.close()

    @property
    def _spool_dir(self) -> Path:
        return self.path / "tmp"

    def _require(self) -> Any:  # noqa: ANN401
        if self._env is None:
            raise RuntimeError(f"LMDBBackend at {self.path} is not open")
        return self._env

    def _begin(self, *, write: bool = False) -> Any:  # noqa: ANN401
        return self._require().begin(write=write, buffers=not write)

    def _store(self, blob_id: str, staged: Staged, mime: str, name: str) -> BlobInfo:
        env = self._require()
        with _value(staged, self.max_size) as value:
            size = len(value)
            info = BlobInfo(id=blob_id, size=size, mime=mime, name=name, created_at=time.time())
            key = blob_id.encode()
            # A reader slot left by a dead process pins every page freed since
            # it began; clearing them before a write keeps the file from growing.
            env.reader_check()
            with self._write_lock, env.begin(write=True) as txn:
                if not txn.put(key, value, db=self._data, overwrite=False):
                    raise BlobExists(blob_id)
                txn.put(key, json.dumps(info.to_dict()).encode(), db=self._meta)
        return info

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes."""
        check_id(blob_id)
        with self._begin() as txn:
            raw = txn.get(blob_id.encode(), db=self._meta)
            if raw is None:
                raise BlobNotFound(blob_id)
            return BlobInfo.from_dict(json.loads(bytes(raw)))

    def exists(self, blob_id: str) -> bool:
        """Whether a whole blob sits under the id."""
        check_id(blob_id)
        with self._begin() as txn:
            return txn.get(blob_id.encode(), db=self._meta) is not None

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, copied out of the map in one piece."""
        check_id(blob_id)
        check_range(start, end)
        with self._begin() as txn:
            value = txn.get(blob_id.encode(), db=self._data)
            if value is None:
                raise BlobNotFound(blob_id)
            lo, hi = clamp(start, end, len(value))
            return bytes(value[lo:hi])

    def stream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
    ) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time.

        Each piece is its own read txn, so the blob is looked up again at every
        pull: one gone or replaced since the first raises ``BlobNotFound``.
        """
        check_id(blob_id)
        check_range(start, end, step)
        return self._pieces(blob_id.encode(), start, end, step)

    def _pieces(self, key: bytes, start: int, end: int | None, step: int) -> Iterator[bytes]:
        # The meta record, written in the same txn as the bytes, names one put:
        # a later pull that finds another (or none) never splices two blobs.
        meta: bytes | None = None
        pos = stop = 0
        while True:
            with self._begin() as txn:
                value = txn.get(key, db=self._data)
                found = txn.get(key, db=self._meta)
                if value is None or found is None or (meta is not None and found != meta):
                    raise BlobNotFound(key.decode())
                if meta is None:
                    meta = bytes(found)
                    pos, stop = clamp(start, end, len(value))
                if pos >= stop:
                    return
                piece = bytes(value[pos : min(pos + step, stop)])
            if not piece:
                return
            # Yielded outside the txn: no reader slot is held while the consumer waits.
            yield piece
            pos += len(piece)

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one."""
        check_id(blob_id)
        key = blob_id.encode()
        env = self._require()
        with self._write_lock, env.begin(write=True) as txn:
            found = txn.delete(key, db=self._data)
            txn.delete(key, db=self._meta)
            return bool(found)


@dataclass
class _Shared:
    """One env open in this process, and how many instances hold it."""

    env: Any
    data: Any
    meta: Any
    write_lock: threading.Lock
    map_size: int
    max_readers: int
    writemap: bool
    count: int = 0


_SHARED: dict[str, _Shared] = {}
"""The env open on each real path in this process."""

_SHARED_LOCK = threading.Lock()
"""Guards ``_SHARED``: every open and close of an env passes through it."""


@contextmanager
def _value(staged: Staged, limit: int) -> Iterator[Any]:
    """The staged bytes as one buffer LMDB copies from: the memory, or an mmap of the file."""
    if staged.buffer is not None:
        if len(staged.buffer) > limit:
            raise BlobTooLarge(f"blob of {len(staged.buffer)} bytes, over the {limit} byte cap")
        yield staged.buffer
        return
    assert staged.path is not None  # noqa: S101 (Staged holds a buffer or a path)
    with staged.path.open("rb") as file:
        size = os.fstat(file.fileno()).st_size
        if size > limit:
            raise BlobTooLarge(f"blob of {size} bytes, over the {limit} byte cap")
        if size == 0:
            yield b""  # an empty file cannot be mapped
            return
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            yield mapped
