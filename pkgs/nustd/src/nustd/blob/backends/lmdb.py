"""Blobs in one LMDB environment, each cut into fixed size chunks under its id."""

from __future__ import annotations

import asyncio
import json
import mmap
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .._base import (
    ThreadedBackend,
    _as_buffer,
    _pieces,
    _source_kind,
    _too_large,
    check_id,
    check_range,
    clamp,
    settled,
)
from ..protocol import STEP, BlobExists, BlobInfo, BlobNotFound


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterator

    from ..protocol import Source


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_MAP_SIZE",
    "DEFAULT_MAX_READERS",
    "DEFAULT_WRITEMAP",
    "MAX_CHUNK",
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

DEFAULT_CHUNK_SIZE = 8 << 20
"""8 MiB per chunk.

Measured on 512 MiB to 2 GiB puts, macOS and Linux: chunks of 1 to 32 MiB
write at the same speed once batched, and read within 20% of each other at
GB/s, far past any network. 8 MiB keeps a 100 GB blob near 12,000 keys.
"""

DEFAULT_BATCH_SIZE = 32 << 20
"""32 MiB of chunks per write txn.

Every commit syncs to disk: about 35 ms on macOS (``F_FULLFSYNC``), a few ms
on Linux. Measured with 8 MiB chunks: a txn per chunk writes 170 MiB/s on
macOS, 32 MiB batches 440 MiB/s, 64 MiB 620 MiB/s; Linux levels off at 32
MiB. A streamed put holds one batch in memory, so 32 MiB is the trade.
"""

MAX_CHUNK = (1 << 31) - 1
"""The biggest chunk: macOS refuses one ``write`` past ``INT_MAX``.

Without writemap LMDB writes a value at commit in one call, so a chunk past
this fails the commit with ``EINVAL``. LMDB's own value cap, 4 GiB, is above
it.
"""

_INDEX = 8
"""Bytes of a chunk's index in its key, big-endian, so a blob's chunks sort in order."""


class LMDBBackend(ThreadedBackend):
    """Blobs in one LMDB environment: each cut into chunks, ranges read straight from the map.

    Three named dbs. ``data`` holds the chunks, keyed by the id's 16 raw bytes
    and the chunk's index (8 bytes, big-endian), so a blob's chunks sit
    together in key order and a range is one cursor walk. ``meta`` holds id
    to json: the ``BlobInfo`` and the blob's chunk size, so a store can mix
    chunk sizes and the default can change. ``claims`` holds the ids whose
    put is still writing, with the writer's pid.

    A put fills chunks as the source is read and commits them in batches,
    each batch its own short write txn. The meta goes in with the last batch:
    a blob is visible exactly while its meta exists, so it shows up whole or
    not at all. A put that fits one batch is one txn and writes no claim.

    Write-once: a put that needs more than one batch claims its id in the
    same txn as its first chunks, under the env's write lock. The claim is
    refused when the id has a meta or a live claim, so a racing put of a
    taken id raises ``BlobExists`` before it writes a chunk, and two puts
    never mix chunks. Every later batch checks the claim is still its own;
    the last one drops it with the meta written. A put that fails deletes
    its chunks and its claim.

    Limits, all native to LMDB:

    - A blob is limited by ``map_size`` alone. A chunk holds at most
      ``MAX_CHUNK`` bytes (just under 2 GiB); ``chunk_size`` is checked
      against it.
    - Memory per put: a buffer or a path goes in as slices of itself (a path
      from an mmap of the caller's file), so it costs nothing beyond LMDB's
      own. A file, an iterable or an async iterable holds up to one batch,
      ``batch_size`` bytes, in Python memory before each commit.
    - A path source is put from an mmap of the caller's file. It must not be
      truncated while its put runs: touching a mapped page past the new end
      kills the process with SIGBUS, not a Python exception.
    - Each batch holds the env's single writer lock for its commit: puts from
      every process take turns batch by batch. Readers never wait. Within one
      process, writes also pass through a ``threading.Lock`` first: py-lmdb
      hangs every thread when one write txn aborts while another thread
      waits to begin one, and a put that loses an id race aborts.
    - A process that dies mid-put leaves its chunks and its claim, invisible.
      They are swept the first time a process opens the env, and before then
      by the next put or ``delete`` of that id. A claim is dead when its pid
      is no longer running (``os.kill(pid, 0)``), as LMDB judges its own
      reader slots; a pid reused since keeps the claim until it exits.
    - The env must be on local disk, never NFS (mmap plus a lock file), and
      every process on it in one pid namespace. LMDB allows one open env per
      path per process, so every instance on one path in a process shares
      one env and one write lock, counted: the last ``close`` closes it. An
      instance whose ``map_size``, ``max_readers`` or ``writemap`` differ
      from the env already open on its path raises ``ValueError`` at
      ``open``. Start children with ``spawn``: an env open across a ``fork``
      is unsafe.
    - ``map_size`` is fixed while open: a full map raises ``lmdb.MapFullError``
      and growing it means reopening in every process.
    - With ``writemap`` (the default on Linux) a put copies straight into
      the map. Without it LMDB first builds each batch in C heap pages, so a
      put costs one batch of RAM there too. The price of ``writemap``:
      ``data.mdb`` is sized to ``map_size`` up front. It stays sparse (only
      written pages take disk), but it reads as 1 TiB to ``ls`` and to copy
      tools that do not keep holes, and needs a filesystem with sparse files.
      On macOS it is off by default: there every writemap commit costs time
      in proportion to ``map_size`` (see ``DEFAULT_WRITEMAP``).
    - A stream opens a short read txn per piece and copies only that piece, so
      a slow consumer pins no pages and holds no reader slot between pulls.
      The price: a blob deleted mid-stream raises ``BlobNotFound`` at the next
      pull, and so does one deleted and put again under the same id.
    - Stores of the earlier layout, one value per id, are not read.

    Args:
        path: the env directory, made on first open.
        map_size: bytes of address space; the env cannot grow past it while
            open.
        max_readers: reader slots shared by every process on the env.
        writemap: put straight into the map rather than through C heap pages.
        chunk_size: bytes per chunk of the blobs this instance puts, at most
            ``MAX_CHUNK``. Each blob keeps the size it was put with.
        batch_size: bytes of chunks per write txn, at least one chunk.
    """

    max_size: int | None = None
    """The most bytes one blob may hold: none of the backend's own beyond ``map_size``."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        map_size: int = DEFAULT_MAP_SIZE,
        max_readers: int = DEFAULT_MAX_READERS,
        writemap: bool = DEFAULT_WRITEMAP,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        if not 1 <= chunk_size <= MAX_CHUNK:
            raise ValueError(f"chunk_size must be within [1, {MAX_CHUNK}], got {chunk_size}")
        if batch_size < 1:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        self.path = Path(path)
        self.map_size = map_size
        self.max_readers = max_readers
        self.writemap = writemap
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self._env: Any = None
        self._data: Any = None
        self._meta: Any = None
        self._claims: Any = None
        self._write_lock: Any = None
        self._key: str | None = None

    def open(self) -> None:
        """Open the env, creating it and its dbs on first use.

        Shares the env another instance in this process already holds open on
        the same path. The first open in a process sweeps what dead puts left.
        """
        if self._env is not None:
            return
        self.path.mkdir(parents=True, exist_ok=True)
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
        self._claims, self._write_lock = shared.claims, shared.write_lock

    def _open_env(self) -> _Shared:
        try:
            import lmdb
        except ImportError as error:
            raise ImportError("LMDBBackend needs lmdb: install nustd[blob]") from error
        env = lmdb.open(
            str(self.path),
            map_size=self.map_size,
            max_dbs=3,
            max_readers=self.max_readers,
            writemap=self.writemap,
            subdir=True,
        )
        try:
            shared = _Shared(
                env=env,
                data=env.open_db(b"data"),
                meta=env.open_db(b"meta"),
                claims=env.open_db(b"claims"),
                write_lock=threading.Lock(),
                map_size=self.map_size,
                max_readers=self.max_readers,
                writemap=self.writemap,
            )
            env.reader_check()
            _sweep(shared)
        except BaseException:
            env.close()
            raise
        return shared

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
        self._env = self._data = self._meta = self._claims = self._write_lock = None
        self._key = None
        with _SHARED_LOCK:
            shared = _SHARED[key]  # type: ignore[index]
            shared.count -= 1
            if shared.count == 0:
                del _SHARED[key]  # type: ignore[arg-type]
                shared.env.close()

    def _require(self) -> Any:  # noqa: ANN401
        if self._env is None:
            raise RuntimeError(f"LMDBBackend at {self.path} is not open")
        return self._env

    def _begin(self, *, write: bool = False) -> Any:  # noqa: ANN401
        return self._require().begin(write=write, buffers=not write)

    # ---- puts --------------------------------------------------------------------------------

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
    ) -> BlobInfo:
        """Store the bytes once under an id, a batch of chunks per write txn.

        Nothing spools: a buffer or a path goes in as slices of itself, a file
        or an iterable a batch at a time as it is read.
        """
        kind = _source_kind(source)
        self._require()
        blob_id = self._claim(blob_id)
        writer = _Put(self, blob_id, mime, name)
        try:
            if kind == "buffer":
                return writer.write_view(_as_buffer(source))  # type: ignore[arg-type]
            if kind == "path":
                return _put_path(writer, Path(source))  # type: ignore[arg-type]
            for piece in _pieces(source):
                writer.feed(piece)
                while writer.fill():
                    writer.commit(last=False)
            return writer.commit(last=True)
        except BaseException:
            writer.abort()
            raise

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
    ) -> BlobInfo:
        """Fill chunks as the iterable yields; commit each batch off the event loop."""
        self._require()
        blob_id = await asyncio.to_thread(self._claim, blob_id)
        writer = _Put(self, blob_id, mime, name)
        try:
            async for piece in source:
                writer.feed(piece)
                while writer.fill():
                    await settled(asyncio.to_thread(writer.commit, last=False))
            return await settled(asyncio.to_thread(writer.commit, last=True))
        except BaseException:
            await asyncio.to_thread(writer.abort)
            raise

    # ---- reads -------------------------------------------------------------------------------

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
            found = txn.get(blob_id.encode(), db=self._meta)
            if found is None:
                raise BlobNotFound(blob_id)
            record = json.loads(bytes(found))
            lo, hi = clamp(start, end, record["size"])
            return self._copy(txn, blob_id, record["chunk"], lo, hi)

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
        return self._pieces(blob_id, start, end, step)

    def _pieces(self, blob_id: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
        # The meta record, written in the same txn as the last chunks, names one
        # put: a later pull that finds another (or none) never splices two blobs.
        key = blob_id.encode()
        meta: bytes | None = None
        chunk = pos = stop = 0
        while True:
            with self._begin() as txn:
                found = txn.get(key, db=self._meta)
                if found is None or (meta is not None and found != meta):
                    raise BlobNotFound(blob_id)
                if meta is None:
                    meta = bytes(found)
                    record = json.loads(meta)
                    chunk = record["chunk"]
                    pos, stop = clamp(start, end, record["size"])
                if pos >= stop:
                    return
                piece = self._copy(txn, blob_id, chunk, pos, min(pos + step, stop))
            # Yielded outside the txn: no reader slot is held while the consumer waits.
            yield piece
            pos += len(piece)

    def _copy(self, txn: Any, blob_id: str, chunk: int, lo: int, hi: int) -> bytes:  # noqa: ANN401
        """``[lo, hi)`` of the blob, copied out of its chunks by one cursor walk."""
        if lo >= hi:
            return b""
        raw = bytes.fromhex(blob_id)
        index, offset = divmod(lo, chunk)
        cursor = txn.cursor(db=self._data)
        parts = []
        need = hi - lo
        found = cursor.set_key(_chunk_key(raw, index))
        while need:
            if not found or cursor.key() != _chunk_key(raw, index):
                # The meta promised this chunk: a blob deleted and put again
                # between the meta read and here cannot happen in one txn, so
                # only a damaged store lands here.
                raise BlobNotFound(blob_id)
            part = cursor.value()[offset : offset + need]
            parts.append(part)
            need -= len(part)
            offset = 0
            index += 1
            found = need > 0 and cursor.next()
        return bytes(parts[0]) if len(parts) == 1 else b"".join(parts)

    # ---- delete ------------------------------------------------------------------------------

    def delete(self, blob_id: str) -> bool:
        """Remove the blob, its chunks in the same txn; whether there was one.

        Also clears what a dead put left under the id. A put still writing is
        left alone.
        """
        check_id(blob_id)
        key = blob_id.encode()
        raw = bytes.fromhex(blob_id)
        env = self._require()
        with self._write_lock, env.begin(write=True) as txn:
            if txn.get(key, db=self._meta) is not None:
                txn.delete(key, db=self._meta)
                _clear(txn, self._data, raw)
                return True
            claim = txn.get(key, db=self._claims)
            if claim is not None and not _alive(claim):
                txn.delete(key, db=self._claims)
                _clear(txn, self._data, raw)
            return False


class _Put:
    """One put's trip into the env: chunks filled, then committed a batch per write txn.

    A buffer or a path hands in slices of itself; a streamed source fills
    chunks of its own. Not thread safe: one put runs one call at a time, the
    async one in turns between the event loop and a thread.
    """

    def __init__(self, backend: LMDBBackend, blob_id: str, mime: str, name: str) -> None:
        self._backend = backend
        self._id = blob_id
        self._key = blob_id.encode()
        self._raw = bytes.fromhex(blob_id)
        self._chunk = backend.chunk_size
        self._per_batch = max(1, backend.batch_size // backend.chunk_size)
        self._mime = mime
        self._name = name
        self._created_at = time.time()
        self._size = 0
        self._index = 0
        self._pending: list[Any] = []
        self._filling = bytearray()
        self._rest = memoryview(b"")
        self._claim: bytes | None = None
        """This put's claim record, once a batch landed before the last."""

    def _count(self, size: int) -> None:
        self._size += size
        error = _too_large(self._size, self._backend.max_size)
        if error is not None:
            raise error

    def feed(self, piece: object) -> None:
        """Take in the next piece of a streamed source; ``fill`` moves it into chunks."""
        view = memoryview(piece).cast("B")  # type: ignore[arg-type]
        self._count(view.nbytes)
        self._rest = view

    def fill(self) -> bool:
        """Move the fed piece into chunks; True when a batch is full and due a commit first.

        Call again after the commit, until False: a piece bigger than a batch
        goes in over several.
        """
        view = self._rest
        while view.nbytes and len(self._pending) < self._per_batch:
            take = min(self._chunk - len(self._filling), view.nbytes)
            self._filling += view[:take]
            view = view[take:]
            if len(self._filling) == self._chunk:
                self._pending.append(self._filling)
                self._filling = bytearray()
        self._rest = view
        return len(self._pending) == self._per_batch

    def write_view(self, view: memoryview) -> BlobInfo:
        """Put a whole buffer, as slices of it: nothing is copied before LMDB's own copy."""
        self._count(view.nbytes)
        try:
            for offset in range(0, view.nbytes, self._chunk):
                if len(self._pending) == self._per_batch:
                    self.commit(last=False)
                self._pending.append(view[offset : offset + self._chunk])
            return self.commit(last=True)
        finally:
            # Slices of an mmap keep it open; drop them on every way out.
            self._pending.clear()

    def commit(self, *, last: bool) -> BlobInfo:
        """Write the pending chunks in one txn; the last one also writes the meta."""
        backend = self._backend
        env = backend._require()
        chunks = self._pending
        if last and self._filling:
            chunks.append(self._filling)
        if self._claim is None:
            # A reader slot left by a dead process pins every page freed since
            # it began; clearing them before the first write keeps the file small.
            env.reader_check()
        info = BlobInfo(
            id=self._id,
            size=self._size,
            mime=self._mime,
            name=self._name,
            created_at=self._created_at,
        )
        claim = self._claim
        with backend._write_lock, env.begin(write=True) as txn:
            if claim is None:
                self._take(txn)
                if not last:
                    claim = json.dumps({"pid": os.getpid(), "token": uuid.uuid4().hex}).encode()
                    txn.put(self._key, claim, db=backend._claims)
            elif txn.get(self._key, db=backend._claims) != self._claim:
                raise BlobExists(self._id)  # swept as dead and taken: not ours anymore
            index = self._index
            for chunk in chunks:
                txn.put(_chunk_key(self._raw, index), chunk, db=backend._data)
                index += 1
            if last:
                record = {**info.to_dict(), "chunk": self._chunk}
                txn.put(self._key, json.dumps(record).encode(), db=backend._meta)
                if claim is not None:
                    txn.delete(self._key, db=backend._claims)
        self._index = index
        self._pending = []
        if last:
            self._claim = None
            self._filling = bytearray()
        else:
            self._claim = claim
        return info

    def _take(self, txn: Any) -> None:  # noqa: ANN401
        """Check the id is free inside the write txn; a dead put's leftovers are swept."""
        backend = self._backend
        if txn.get(self._key, db=backend._meta) is not None:
            raise BlobExists(self._id)
        claim = txn.get(self._key, db=backend._claims)
        if claim is not None:
            if _alive(claim):
                raise BlobExists(self._id)
            txn.delete(self._key, db=backend._claims)
            _clear(txn, backend._data, self._raw)

    def abort(self) -> None:
        """Delete what this put committed, when it still holds its claim."""
        self._pending = []
        self._filling = bytearray()
        claim, self._claim = self._claim, None
        if claim is None:
            return  # nothing committed, or the last commit landed
        backend = self._backend
        with backend._write_lock, backend._require().begin(write=True) as txn:
            if txn.get(self._key, db=backend._claims) == claim:
                txn.delete(self._key, db=backend._claims)
                _clear(txn, backend._data, self._raw)


def _put_path(writer: _Put, path: Path) -> BlobInfo:
    """Put a file from an mmap of it, never read into Python memory."""
    with path.open("rb") as file:
        if os.fstat(file.fileno()).st_size == 0:
            return writer.write_view(memoryview(b""))  # an empty file cannot be mapped
        mapped = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            return writer.write_view(memoryview(mapped))
        finally:
            try:
                mapped.close()
            except BufferError:
                pass  # a traceback still holds a slice: the map closes once it is collected


def _chunk_key(raw: bytes, index: int) -> bytes:
    return raw + index.to_bytes(_INDEX, "big")


def _clear(txn: Any, data: Any, raw: bytes) -> None:  # noqa: ANN401
    """Delete every chunk of one id: its key range, by one cursor walk."""
    cursor = txn.cursor(db=data)
    if not cursor.set_range(raw):
        return
    while cursor.key()[: len(raw)] == raw:
        if not cursor.delete():
            return


def _alive(claim: bytes | memoryview) -> bool:
    """Whether the process that wrote a claim still runs."""
    pid = json.loads(bytes(claim))["pid"]
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # running, as another user
    return True


def _sweep(shared: _Shared) -> None:
    """Clear the chunks and claims of puts whose process died; no write txn when none did."""
    with shared.env.begin(db=shared.claims) as txn:
        dead = [bytes(key) for key, claim in txn.cursor() if not _alive(claim)]
    if not dead:
        return
    with shared.write_lock, shared.env.begin(write=True) as txn:
        for key in dead:
            claim = txn.get(key, db=shared.claims)
            if claim is not None and not _alive(claim):
                txn.delete(key, db=shared.claims)
                _clear(txn, shared.data, bytes.fromhex(key.decode()))


@dataclass
class _Shared:
    """One env open in this process, and how many instances hold it."""

    env: Any
    data: Any
    meta: Any
    claims: Any
    write_lock: threading.Lock
    map_size: int
    max_readers: int
    writemap: bool
    count: int = 0


_SHARED: dict[str, _Shared] = {}
"""The env open on each real path in this process."""

_SHARED_LOCK = threading.Lock()
"""Guards ``_SHARED``: every open and close of an env passes through it."""
