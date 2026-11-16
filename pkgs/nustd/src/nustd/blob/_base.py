"""What the backends share: ids, ranges, spooling and the async twins run in a thread."""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
import uuid
from collections.abc import AsyncIterable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .protocol import STEP, BlobExists, BlobInfo, BlobTooLarge


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from .protocol import AsyncSource, Source


__all__ = [
    "LocalBackend",
    "Staged",
    "ThreadedBackend",
    "aspool",
    "check_id",
    "check_range",
    "clamp",
    "new_id",
    "spool",
]


_ID = re.compile(r"[0-9a-f]{32}")


def new_id() -> str:
    """A fresh blob id."""
    return uuid.uuid4().hex


def check_id(blob_id: object) -> str:
    """The id, checked to have the one shape a blob id may have.

    Any other id raises ``ValueError``. The shape is what keeps an id from naming a path outside a store, so it is
    checked before an id reaches a backend.
    """
    if not isinstance(blob_id, str) or _ID.fullmatch(blob_id) is None:
        raise ValueError(f"a blob id is 32 lowercase hex characters, got {blob_id!r}")
    return blob_id


def check_range(start: int, end: int | None, step: int = STEP) -> None:
    """Refuse a negative bound or a step that would never move."""
    if start < 0 or (end is not None and end < 0):
        raise ValueError(f"a range bound cannot be negative, got [{start}, {end})")
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")


def clamp(start: int, end: int | None, size: int) -> tuple[int, int]:
    """The half-open range cut to ``[0, size)``.

    An inverted range comes back empty.
    """
    start = min(start, size)
    end = size if end is None else min(end, size)
    return start, max(start, end)


@dataclass(frozen=True)
class Staged:
    """A put's bytes, made ready for a backend to take in.

    Exactly one of ``buffer`` and ``path`` is set. A path is ``owned`` when it
    is a spool file of ours, in the backend's spool directory: the backend may
    link it into place, and it is unlinked after the store either way. A path
    that is not owned is the caller's file, read and never moved.
    """

    buffer: memoryview | None = None
    path: Path | None = None
    owned: bool = False


def _source_kind(source: object) -> str:
    """Which way a put takes the source in.

    A source it cannot take raises ``TypeError``.
    """
    if isinstance(source, str):
        raise TypeError("a str source is ambiguous (text or a path?): pass bytes or a Path")
    if isinstance(source, (bytes, bytearray, memoryview)):
        return "buffer"
    if isinstance(source, os.PathLike):
        return "path"
    if hasattr(source, "read"):
        return "file"
    if isinstance(source, Iterable):
        return "iterable"
    if isinstance(source, AsyncIterable):
        raise TypeError("an async iterable source needs aput, not put")
    raise TypeError(f"cannot put a {type(source).__name__}")


def _as_buffer(source: bytes | bytearray | memoryview) -> memoryview:
    view = memoryview(source)
    if not view.c_contiguous:
        raise TypeError("a memoryview source must be contiguous")
    return view.cast("B")


def _too_large(size: int, limit: int | None) -> BlobTooLarge | None:
    if limit is not None and size > limit:
        return BlobTooLarge(f"blob of {size} bytes, over the backend's {limit} byte cap")
    return None


def _pieces(source: object) -> Iterator[object]:
    """A file or an iterable as pieces.

    A file is read ``STEP`` at a time.
    """
    if hasattr(source, "read"):
        while True:
            piece = source.read(STEP)  # type: ignore[attr-defined]
            if not piece:
                if not isinstance(piece, (bytes, bytearray)):
                    memoryview(piece)  # a text file ends on "", refused here as str
                return
            yield piece
    else:
        yield from source  # type: ignore[misc]


def _new_spool(directory: Path) -> tuple[int, Path]:
    fd, name = tempfile.mkstemp(dir=directory, prefix="spool-")
    return fd, Path(name)


def spool(source: Source, directory: Path, *, limit: int | None = None) -> Path:
    """Write a file or an iterable of bytes to a fresh temp file, piece by piece.

    Nothing is left behind when the source raises or overflows ``limit``.

    Args:
        source: a binary file, or an iterable of bytes-like pieces.
        directory: where the temp file goes. Keep it on the store's disk, so a
            backend can link the file into place.
        limit: the byte cap; ``BlobTooLarge`` as soon as the source passes it.
    """
    fd, path = _new_spool(directory)
    try:
        with os.fdopen(fd, "wb") as out:
            size = 0
            for piece in _pieces(source):
                size += memoryview(piece).nbytes  # type: ignore[arg-type]
                error = _too_large(size, limit)
                if error is not None:
                    raise error
                out.write(piece)  # type: ignore[arg-type]
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


async def aspool(
    source: AsyncIterable[bytes],
    directory: Path,
    *,
    limit: int | None = None,
) -> Path:
    """``spool`` for an async iterable.

    Every disk write runs in a thread.
    """
    fd, path = _new_spool(directory)
    out = os.fdopen(fd, "wb")
    try:
        size = 0
        async for piece in source:
            size += memoryview(piece).nbytes
            error = _too_large(size, limit)
            if error is not None:
                raise error
            await asyncio.to_thread(out.write, piece)
        await asyncio.to_thread(out.close)
    except BaseException:
        out.close()
        path.unlink(missing_ok=True)
        raise
    return path


class ThreadedBackend:
    """A backend with blocking sync calls, and async twins that run them in a thread.

    A subclass provides ``open``, ``close``, ``put``, ``info``, ``exists``,
    ``read``, ``stream``, ``delete`` and ``_aput_iterable``. The async twins
    and the id claim live here.
    """

    max_size: int | None = None
    """The most bytes one blob may hold, or None for no cap of the backend's own."""

    def open(self) -> None:
        """Open the store."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the store."""
        raise NotImplementedError

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
    ) -> BlobInfo:
        """Store the bytes once under an id."""
        raise NotImplementedError

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes."""
        raise NotImplementedError

    def exists(self, blob_id: str) -> bool:
        """Whether a whole blob sits under the id."""
        raise NotImplementedError

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, in one piece."""
        raise NotImplementedError

    def stream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
    ) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time."""
        raise NotImplementedError

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one."""
        raise NotImplementedError

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
    ) -> BlobInfo:
        """``aput`` of an async iterable, which no thread can pull."""
        raise NotImplementedError

    def _claim(self, blob_id: str | None) -> str:
        """The id to put under.

        A taken id fails here, before any byte is read from the source. The
        store's own write-once guard still decides a race.
        """
        if blob_id is None:
            return new_id()
        check_id(blob_id)
        if self.exists(blob_id):
            raise BlobExists(blob_id)
        return blob_id

    async def aput(
        self,
        source: AsyncSource,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
    ) -> BlobInfo:
        """``put``, off the event loop; also takes an async iterable of bytes."""
        if not isinstance(source, AsyncIterable) or isinstance(source, Iterable):
            return await asyncio.to_thread(
                self.put,
                source,  # type: ignore[arg-type]
                blob_id=blob_id,
                mime=mime,
                name=name,
            )
        return await self._aput_iterable(source, blob_id, mime, name)

    async def ainfo(self, blob_id: str) -> BlobInfo:
        """``info``, off the event loop."""
        return await asyncio.to_thread(self.info, blob_id)

    async def aexists(self, blob_id: str) -> bool:
        """``exists``, off the event loop."""
        return await asyncio.to_thread(self.exists, blob_id)

    async def aread(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """``read``, off the event loop."""
        return await asyncio.to_thread(self.read, blob_id, start, end)

    async def astream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
    ) -> AsyncIterator[bytes]:
        """``stream``, each piece read off the event loop."""
        pieces = self.stream(blob_id, start, end, step=step)
        try:
            while True:
                piece = await asyncio.to_thread(next, pieces, None)
                if piece is None:
                    return
                yield piece
        finally:
            try:
                pieces.close()
            except ValueError:
                # Cancelled mid-pull: the thread still runs the generator, so
                # it cannot be closed here; it closes when collected.
                pass

    async def adelete(self, blob_id: str) -> bool:
        """``delete``, off the event loop."""
        return await asyncio.to_thread(self.delete, blob_id)


class LocalBackend(ThreadedBackend):
    """A backend on this machine's disk: every put that is not a buffer or a path spools first.

    A subclass provides ``open``, ``close``, ``info``, ``exists``, ``read``,
    ``stream``, ``delete``, ``_store`` and ``_spool_dir``. The put surface,
    for every source kind, lives here.
    """

    @property
    def _spool_dir(self) -> Path:
        """Where spool files go: on the store's own disk."""
        raise NotImplementedError

    def _store(self, blob_id: str, staged: Staged, mime: str, name: str) -> BlobInfo:
        """Take the staged bytes in under a checked id.

        Raises ``BlobExists`` when the id is taken, checked by the store itself.
        """
        raise NotImplementedError

    def _store_spool(self, blob_id: str, path: Path, mime: str, name: str) -> BlobInfo:
        # The unlink sits with the store so both run in one thread, in order,
        # even when an aput awaiting them is cancelled.
        try:
            return self._store(blob_id, Staged(path=path, owned=True), mime, name)
        finally:
            path.unlink(missing_ok=True)

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
    ) -> BlobInfo:
        """Store the bytes once under an id.

        A file or an iterable spools to disk first.
        """
        kind = _source_kind(source)
        blob_id = self._claim(blob_id)
        if kind == "buffer":
            staged = Staged(buffer=_as_buffer(source))  # type: ignore[arg-type]
            return self._store(blob_id, staged, mime, name)
        if kind == "path":
            return self._store(blob_id, Staged(path=Path(source)), mime, name)  # type: ignore[arg-type]
        path = spool(source, self._spool_dir, limit=self.max_size)
        return self._store_spool(blob_id, path, mime, name)

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
    ) -> BlobInfo:
        """Spool the iterable as it arrives, then store the spool file."""
        blob_id = await asyncio.to_thread(self._claim, blob_id)
        path = await aspool(source, self._spool_dir, limit=self.max_size)
        return await asyncio.to_thread(self._store_spool, blob_id, path, mime, name)
