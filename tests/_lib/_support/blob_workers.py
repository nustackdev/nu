"""Children for the ``nustd.blob`` tests that run backends in ``spawn``-ed processes.

A ``spawn`` child imports its target by module, so the targets live here, not
in the test files (pytest imports those by path).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from nustd.blob import BlobExists, FilesBackend, LMDBBackend, S3Backend


if TYPE_CHECKING:
    from collections.abc import Iterator
    from multiprocessing.queues import Queue
    from multiprocessing.synchronize import Barrier


__all__ = [
    "BUCKET",
    "CONTESTED",
    "KINDS",
    "LOCAL_KINDS",
    "blob_id",
    "content",
    "make",
    "putter",
    "race_content",
    "racer",
    "stalled_putter",
    "writer",
]


LOCAL_KINDS = ["lmdb", "files"]
"""The backends on this machine's disk, which a spawned child can open too."""

KINDS = [*LOCAL_KINDS, "s3"]
"""Every backend. The s3 one runs on moto, inside the test process only."""

BUCKET = "nu-blob-test"
"""The moto bucket the s3 tests put into."""

CONTESTED = "f" * 32
"""An id every writer tries to put; exactly one must win."""


def make(kind: str, path: Path) -> LMDBBackend | FilesBackend | S3Backend:
    """A backend of ``kind`` at ``path``, not yet open.

    An s3 backend takes the path's last part as its key prefix, in ``BUCKET``.
    """
    if kind == "s3":
        return S3Backend(BUCKET, prefix=f"{path.name}/")
    if kind == "lmdb":
        return LMDBBackend(path)
    if kind == "files":
        return FilesBackend(path)
    raise ValueError(kind)


def blob_id(worker: int, index: int) -> str:
    """A fixed id per (worker, index), so each side knows the other's ids."""
    return f"{worker:x}{index:031x}"


def content(worker: int, index: int) -> bytes:
    """Bytes of a few KiB to a few hundred KiB, different per (worker, index)."""
    seed = hashlib.sha256(f"{worker}:{index}".encode()).digest()
    return seed * (100 + 1000 * index)


def writer(
    kind: str,
    path: str,
    worker: int,
    other: int,
    count: int,
    barrier: Barrier,
    out: Queue,
    precheck: bool = True,
) -> None:
    """Race for ``CONTESTED``, put ``count`` blobs, then read back the other worker's blobs.

    Args:
        precheck: False turns off the put's existence check, so both workers
            reach the store's own write-once guard.
    """
    backend = make(kind, Path(path))
    if not precheck:
        backend.exists = lambda blob_id: False  # type: ignore[method-assign]
    backend.open()
    try:
        barrier.wait()
        try:
            backend.put(content(worker, 0), blob_id=CONTESTED)
            won = True
        except BlobExists:
            won = False
        for index in range(count):
            backend.put(content(worker, index), blob_id=blob_id(worker, index), mime="x/y")
        barrier.wait()
        seen = 0
        for index in range(count):
            bid = blob_id(other, index)
            data = content(other, index)
            assert backend.read(bid) == data
            assert b"".join(backend.stream(bid, step=4096)) == data
            assert backend.info(bid).size == len(data)
            seen += 1
        out.put((worker, won, seen))
    finally:
        backend.close()


def putter(kind: str, path: str, size: int, ready: Queue, go: Queue, batch: int) -> None:
    """Put ``size`` bytes from a generator once told to; for watching the process from outside.

    Args:
        batch: the LMDB batch size, what a streamed put there holds in memory.
    """
    backend = make(kind, Path(path))
    if isinstance(backend, LMDBBackend):
        backend.batch_size = batch
    backend.open()
    try:
        ready.put("ready")
        go.get()
        step = 1 << 20

        def pieces() -> Iterator[bytes]:
            for offset in range(0, size, step):
                yield bytes([offset // step % 256]) * min(step, size - offset)

        info = backend.put(pieces())
        ready.put(info.size)
        go.get()
    finally:
        backend.close()


def race_content(worker: int) -> bytes:
    """What ``racer`` puts: 200 KiB, different per worker."""
    return bytes([worker + 1]) * (200 << 10)


def racer(path: str, worker: int, barrier: Barrier, out: Queue) -> None:
    """Put ``race_content`` under ``CONTESTED`` over many small batches, past the pre-check.

    Both racers claim mid-way through each other's batches, so a put that mixed
    chunks would show.
    """
    backend = LMDBBackend(Path(path), chunk_size=1024, batch_size=4096)
    backend.exists = lambda blob_id: False  # type: ignore[method-assign]
    backend.open()
    try:
        data = race_content(worker)
        barrier.wait()
        try:
            backend.put((data[i : i + 1000] for i in range(0, len(data), 1000)), blob_id=CONTESTED)
            won = True
        except BlobExists:
            won = False
        out.put((worker, won))
    finally:
        backend.close()


def stalled_putter(path: str, blob_id: str, ready: Queue, go: Queue) -> None:
    """Put under ``blob_id`` until a few batches landed, then stall, to be killed there."""
    backend = LMDBBackend(Path(path), chunk_size=1024, batch_size=4096)
    backend.open()

    def pieces() -> Iterator[bytes]:
        yield b"x" * 20_000  # five batches commit before the next pull
        ready.put("stalled")
        go.get()
        yield b"never"

    backend.put(pieces(), blob_id=blob_id)
