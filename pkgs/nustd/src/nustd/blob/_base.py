"""What the backends share: ids, ranges, sources, following reads and the async twins run in a thread."""

from __future__ import annotations

import asyncio
import os
import re
import time
import uuid
from collections.abc import AsyncIterable, Iterable
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

from .protocol import STEP, BlobExists, BlobIdle, BlobInfo, BlobNotFound, BlobTooLarge


if TYPE_CHECKING:
    from collections.abc import (
        AsyncGenerator,
        AsyncIterator,
        Awaitable,
        Callable,
        Generator,
        Iterator,
    )

    from .protocol import AsyncSource, Source


__all__ = [
    "DEFAULT_COMMIT_INTERVAL",
    "POLL_FIRST",
    "POLL_LAST",
    "Busy",
    "LocalBackend",
    "ThreadedBackend",
    "check_id",
    "check_idle",
    "check_range",
    "clamp",
    "new_id",
    "settled",
]


POLL_FIRST = 0.01
"""Seconds a following read first waits before it looks at an open blob again.

Followers poll the blob's meta: there is no cross-process wake-up (a later
option: inotify for files, a pipe or a socket per store). The wait doubles
while the blob does not grow, up to ``POLL_LAST``, and drops back to this
once it does.
"""

DEFAULT_COMMIT_INTERVAL = 0.25
"""Seconds a streamed put or append holds bytes before it commits them, batch full or not.

Size alone would show a slow source to its followers only a batch at a
time (32 MiB on lmdb, 8 MiB on files); the clock shows it within about
this long. A fast source fills its batches first and never waits on the
clock.
"""

POLL_LAST = 0.25
"""The longest wait between two looks of a following read: what a stalled writer costs a follower."""


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


def check_interval(interval: float | None) -> None:
    """Refuse a negative ``commit_interval``; None commits by size alone."""
    if interval is not None and interval < 0:
        raise ValueError(f"commit_interval is seconds, 0 or more, got {interval}")


def check_idle(idle: float | None) -> None:
    """Refuse a negative ``idle``; None waits for ever."""
    if idle is not None and idle < 0:
        raise ValueError(f"idle is seconds, 0 or more, got {idle}")


def clamp(start: int, end: int | None, size: int) -> tuple[int, int]:
    """The half-open range cut to ``[0, size)``.

    An inverted range comes back empty.
    """
    start = min(start, size)
    end = size if end is None else min(end, size)
    return start, max(start, end)


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


_T = TypeVar("_T")


async def settled(call: Awaitable[_T]) -> _T:
    """Await a call run in a thread; when cancelled, still wait for the thread to finish.

    A cleanup sent while a write is still in flight would miss it and leave
    that write behind.
    """
    task = asyncio.ensure_future(call)
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.wait({task})
        raise


class Busy(Exception):  # noqa: N818 - a state, not an error kind
    """Another writer holds the blob: an append or a seal waits for it, then tries again."""


def _acquire(begin: Callable[[], _T], blob_id: str) -> _T:
    """``begin()``, tried again after a wait each time another writer holds the blob."""
    waiter = _Waiter(blob_id, None)
    while True:
        try:
            return begin()
        except Busy:
            time.sleep(waiter.next_wait())


async def _aacquire(
    begin: Callable[[], _T], blob_id: str, release: Callable[[_T], None] | None = None
) -> _T:
    """``_acquire`` with each try in a thread and each wait on the event loop.

    Cancelled while a try runs, it waits for the try and hands what it got
    to ``release``, so nothing stays held.
    """
    waiter = _Waiter(blob_id, None)
    while True:
        task = asyncio.ensure_future(asyncio.to_thread(begin))
        try:
            return await asyncio.shield(task)
        except Busy:
            await asyncio.sleep(waiter.next_wait())
        except asyncio.CancelledError:
            await asyncio.wait({task})
            if release is not None and not task.cancelled() and task.exception() is None:
                release(task.result())
            raise


class _Waiter:
    """When a waiting call looks at its blob again: backoff while nothing moves, ``BlobIdle`` past ``idle``."""

    def __init__(self, blob_id: str, idle: float | None) -> None:
        self._id = blob_id
        self._idle = idle
        self.grew()

    def grew(self) -> None:
        """The blob grew: wait short again, and count idle time from now."""
        self._delay = POLL_FIRST
        self._since = time.monotonic()

    def next_wait(self) -> float:
        """Seconds to wait before the next look; ``BlobIdle`` when the idle time is spent."""
        delay = self._delay
        self._delay = min(self._delay * 2, POLL_LAST)
        if self._idle is None:
            return delay
        left = self._idle - (time.monotonic() - self._since)
        if left <= 0:
            raise BlobIdle(f"blob {self._id} did not grow for {self._idle} s")
        return min(delay, left)


class ThreadedBackend:
    """A backend with blocking sync calls, and async twins that run them in a thread.

    A subclass provides ``open``, ``close``, ``put``, ``append``, ``seal``,
    ``info``, ``exists``, ``delete``, ``_read``, ``_pieces``,
    ``_aput_iterable`` and ``_aappend_iterable``. The reads, the following
    reads, the async twins and the id claim live here.

    A following read polls ``info``: it reads to the size it finds, then
    looks again after a wait that starts at ``POLL_FIRST`` and doubles up to
    ``POLL_LAST`` while the blob does not grow. It ends when the blob is
    sealed (or its ``end`` is reached), raises ``BlobNotFound`` when the blob
    is deleted, or put again under its id, and ``BlobIdle`` after ``idle``
    seconds without growth. The async one waits on the event loop, never in
    a thread, so cancelling it is immediate.
    """

    max_size: int | None = None
    """The most bytes one blob may hold, or None for no cap of the backend's own."""

    supports_open: bool = True
    """Whether the backend holds open blobs."""

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
        seal: bool = True,
    ) -> BlobInfo:
        """Store the bytes under a fresh id."""
        raise NotImplementedError

    def append(self, blob_id: str, source: Source) -> BlobInfo:
        """Add the bytes to the end of an open blob."""
        raise NotImplementedError

    def seal(self, blob_id: str) -> BlobInfo:
        """Close the blob; sealing a sealed one is a no-op."""
        raise NotImplementedError

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes."""
        raise NotImplementedError

    def exists(self, blob_id: str) -> bool:
        """Whether a blob sits under the id, open or sealed."""
        raise NotImplementedError

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one."""
        raise NotImplementedError

    def _read(self, blob_id: str, start: int, end: int | None) -> bytes | None:
        """The bytes of a checked range now, or None when the blob is open and the range runs past its end."""
        raise NotImplementedError

    def _pieces(self, blob_id: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
        """The bytes of a checked range as it is now, ``step`` at a time; never waits."""
        raise NotImplementedError

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
        seal: bool,
    ) -> BlobInfo:
        """``aput`` of an async iterable, which no thread can pull."""
        raise NotImplementedError

    async def _aappend_iterable(self, blob_id: str, source: AsyncIterable[bytes]) -> BlobInfo:
        """``aappend`` of an async iterable, which no thread can pull."""
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

    # ---- reads -------------------------------------------------------------------------------

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, in one piece; on an open blob, once they are all there."""
        check_id(blob_id)
        check_range(start, end)
        data = self._read(blob_id, start, end)
        if data is None:
            return b"".join(self._follow(blob_id, start, end, STEP, None))
        return data

    def stream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
        follow: bool = False,
        idle: float | None = None,
    ) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time; following, until the blob is sealed."""
        check_id(blob_id)
        check_range(start, end, step)
        check_idle(idle)
        if follow and self.supports_open:
            return self._follow(blob_id, start, end, step, idle)
        return self._pieces(blob_id, start, end, step)

    def _follow(
        self, blob_id: str, start: int, end: int | None, step: int, idle: float | None
    ) -> Iterator[bytes]:
        pos = start
        born: float | None = None
        waiter = _Waiter(blob_id, idle)
        while True:
            info = self.info(blob_id)
            if born is None:
                born = info.created_at
            elif info.created_at != born:
                raise BlobNotFound(blob_id)  # deleted, and put again under its id
            stop = info.size if end is None else min(end, info.size)
            if pos < stop:
                for piece in self._pieces(blob_id, pos, stop, step):
                    yield piece
                    pos += len(piece)
                waiter.grew()
                continue
            if info.sealed or (end is not None and pos >= end):
                return
            time.sleep(waiter.next_wait())

    async def _afollow(
        self, blob_id: str, start: int, end: int | None, step: int, idle: float | None
    ) -> AsyncGenerator[bytes, None]:
        pos = start
        born: float | None = None
        waiter = _Waiter(blob_id, idle)
        while True:
            info = await self.ainfo(blob_id)
            if born is None:
                born = info.created_at
            elif info.created_at != born:
                raise BlobNotFound(blob_id)
            stop = info.size if end is None else min(end, info.size)
            if pos < stop:
                async for piece in self._apieces(blob_id, pos, stop, step):
                    yield piece
                    pos += len(piece)
                waiter.grew()
                continue
            if info.sealed or (end is not None and pos >= end):
                return
            await asyncio.sleep(waiter.next_wait())

    # ---- async twins -------------------------------------------------------------------------

    async def aput(
        self,
        source: AsyncSource,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
        seal: bool = True,
    ) -> BlobInfo:
        """``put``, off the event loop; also takes an async iterable of bytes."""
        if not isinstance(source, AsyncIterable) or isinstance(source, Iterable):
            return await asyncio.to_thread(
                self.put,
                source,  # type: ignore[arg-type]
                blob_id=blob_id,
                mime=mime,
                name=name,
                seal=seal,
            )
        return await self._aput_iterable(source, blob_id, mime, name, seal)

    async def aappend(self, blob_id: str, source: AsyncSource) -> BlobInfo:
        """``append``, off the event loop; also takes an async iterable of bytes."""
        if not isinstance(source, AsyncIterable) or isinstance(source, Iterable):
            return await asyncio.to_thread(self.append, blob_id, source)  # type: ignore[arg-type]
        return await self._aappend_iterable(blob_id, source)

    async def aseal(self, blob_id: str) -> BlobInfo:
        """``seal``, off the event loop."""
        return await asyncio.to_thread(self.seal, blob_id)

    async def ainfo(self, blob_id: str) -> BlobInfo:
        """``info``, off the event loop."""
        return await asyncio.to_thread(self.info, blob_id)

    async def aexists(self, blob_id: str) -> bool:
        """``exists``, off the event loop."""
        return await asyncio.to_thread(self.exists, blob_id)

    async def aread(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """``read``, off the event loop; on an open blob it waits on the loop, not in a thread."""
        check_id(blob_id)
        check_range(start, end)
        data = await asyncio.to_thread(self._read, blob_id, start, end)
        if data is None:
            return b"".join(
                [piece async for piece in self._afollow(blob_id, start, end, STEP, None)]
            )
        return data

    async def astream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
        follow: bool = False,
        idle: float | None = None,
    ) -> AsyncIterator[bytes]:
        """``stream``, each piece read off the event loop; a following one waits on it."""
        check_id(blob_id)
        check_range(start, end, step)
        check_idle(idle)
        pieces = (
            self._afollow(blob_id, start, end, step, idle)
            if follow and self.supports_open
            else self._apieces(blob_id, start, end, step)
        )
        try:
            async for piece in pieces:
                yield piece
        finally:
            await pieces.aclose()

    async def _apieces(
        self, blob_id: str, start: int, end: int | None, step: int
    ) -> AsyncGenerator[bytes, None]:
        pieces = cast("Generator[bytes, None, None]", self._pieces(blob_id, start, end, step))
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


class Writer(Protocol):
    """One put's or one append's trip into a local store, as ``LocalBackend`` drives it."""

    def take(self, source: object, kind: str) -> None:
        """Write a whole sync source in, committing as batches fill; the last bytes may wait for ``finish``."""
        ...

    def feed(self, piece: object) -> bool:
        """Hold the next piece of an async source, cheaply, on the event loop; True when a ``flush`` is due."""
        ...

    def due_in(self) -> float | None:
        """Seconds until the bytes held are due a commit by the clock; None when nothing waits."""
        ...

    def flush(self) -> None:
        """Write what ``feed`` holds, committing as batches fill or the clock says: blocking, run in a thread."""
        ...

    def finish(self) -> BlobInfo:
        """Write the rest and commit it, sealed or not as the call asked."""
        ...

    def fail(self) -> None:
        """Undo after an error: a put deletes what it wrote, an append keeps what it committed."""
        ...

    def close(self) -> None:
        """Let go of what the writer holds; after ``finish`` or ``fail``."""
        ...


def _drive(writer: Writer, source: object, kind: str) -> BlobInfo:
    try:
        writer.take(source, kind)
        return writer.finish()
    except BaseException:
        writer.fail()
        raise
    finally:
        writer.close()


async def _adrive(writer: Writer, source: AsyncIterable[bytes]) -> BlobInfo:
    """Feed an async source to the writer, and commit by the clock beside it, while the source waits too.

    Two tasks share the writer under a lock: one pulls the source and feeds
    it, the other sleeps until the bytes held are due (``due_in``) and
    flushes them. Neither cancels the source, and a piece costs no task of
    its own. The first to fail stops the other.
    """
    lock = asyncio.Lock()
    fed = asyncio.Event()

    async def feed() -> None:
        async for piece in source:
            async with lock:
                if writer.feed(piece):
                    await settled(asyncio.to_thread(writer.flush))
            fed.set()

    async def clock() -> None:
        while True:
            fed.clear()  # before the look, so a piece fed after it wakes the wait
            left = writer.due_in()
            if left is None:
                await fed.wait()
                continue
            await asyncio.sleep(left)
            async with lock:
                if writer.due_in() == 0:
                    await settled(asyncio.to_thread(writer.flush))

    feeding = asyncio.ensure_future(feed())
    ticking = asyncio.ensure_future(clock())
    try:
        try:
            await asyncio.wait({feeding, ticking}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (feeding, ticking):
                if not task.done():
                    task.cancel()
            await asyncio.wait({feeding, ticking})
        if not ticking.cancelled() and ticking.exception() is not None:
            raise ticking.exception()  # type: ignore[misc]
        feeding.result()
        return await settled(asyncio.to_thread(writer.finish))
    except BaseException:
        await asyncio.to_thread(writer.fail)
        raise
    finally:
        writer.close()


def _release(writer: Writer) -> None:
    writer.fail()
    writer.close()


class LocalBackend(ThreadedBackend):
    """A backend on this machine that writes through a ``Writer`` of its own.

    A subclass provides ``_create``, ``_begin_append`` and ``_seal_once``
    besides the reads. Put, append and seal, sync and async, live here.

    One writer at a time per blob: ``_begin_append`` and ``_seal_once``
    raise ``Busy`` while another put or append holds the blob, and the call
    waits (``POLL_FIRST`` doubling up to ``POLL_LAST``) and tries again. The
    async calls wait on the event loop, so a cancelled one stops waiting at once.
    """

    def _create(self, blob_id: str, mime: str, name: str, seal: bool) -> Writer:
        """A writer for a put under a free id; ``BlobExists`` when the store finds it taken."""
        raise NotImplementedError

    def _begin_append(self, blob_id: str) -> Writer:
        """A writer holding an open blob; ``Busy``, ``BlobNotFound`` or ``BlobSealed`` when it cannot."""
        raise NotImplementedError

    def _seal_once(self, blob_id: str) -> BlobInfo:
        """Seal the blob unless another writer holds it (``Busy``)."""
        raise NotImplementedError

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
        seal: bool = True,
    ) -> BlobInfo:
        """Store the bytes under a fresh id, committed a batch at a time as the source is read."""
        kind = _source_kind(source)
        blob_id = self._claim(blob_id)
        return _drive(self._create(blob_id, mime, name, seal), source, kind)

    def append(self, blob_id: str, source: Source) -> BlobInfo:
        """Add the bytes to the end of an open blob, once no other writer holds it."""
        check_id(blob_id)
        kind = _source_kind(source)
        writer = _acquire(lambda: self._begin_append(blob_id), blob_id)
        return _drive(writer, source, kind)

    def seal(self, blob_id: str) -> BlobInfo:
        """Close the blob once no other writer holds it; a sealed one is left as it is."""
        check_id(blob_id)
        return _acquire(lambda: self._seal_once(blob_id), blob_id)

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
        seal: bool,
    ) -> BlobInfo:
        """Hold the pieces as the iterable yields them; write each batch off the event loop."""
        blob_id = await asyncio.to_thread(self._claim, blob_id)
        bid = blob_id
        writer = await _aacquire(lambda: self._create(bid, mime, name, seal), bid, _release)
        return await _adrive(writer, source)

    async def aappend(self, blob_id: str, source: AsyncSource) -> BlobInfo:
        """``append``, off the event loop; waits for another writer on it."""
        check_id(blob_id)
        if isinstance(source, AsyncIterable) and not isinstance(source, Iterable):
            writer = await _aacquire(lambda: self._begin_append(blob_id), blob_id, _release)
            return await _adrive(writer, source)
        kind = _source_kind(source)
        writer = await _aacquire(lambda: self._begin_append(blob_id), blob_id, _release)
        return await settled(asyncio.to_thread(_drive, writer, source, kind))

    async def aseal(self, blob_id: str) -> BlobInfo:
        """``seal``, off the event loop; waits for another writer on it."""
        check_id(blob_id)
        return await _aacquire(lambda: self._seal_once(blob_id), blob_id)
