"""Lock and Hold: brackets that guard a body with a file on a mount.

``Lock`` takes an exclusive ``fcntl.lockf`` lock on a file for the body's
span, so one holder runs at a time across processes, and across machines
on NFS, which carries ``lockf`` locks (never ``flock``). ``Hold`` writes a
file for the body's span and removes it on the way out, unless someone
else's text has replaced it by then.

Both take a ``FileRef``, the file on its mount, and carry the mount and the
path as config children, so the path can be a term computed when the
bracket opens. A sync run takes and releases in place; an async run does
the file work in a thread and waits for a lock on the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import math
import time
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.lang import Bracket, Nu

from .errors import FsLocked
from .interactions import fabric_of
from .refs import FileRef


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from nu.lang.runtime import Context

    from .fabric import FsFabric


__all__ = ["POLL", "Hold", "Lock"]


#: Seconds between tries while a waiting ``Lock`` finds the lock taken.
POLL = 0.05


def _file(file: object, who: str) -> FileRef:
    if not isinstance(file, FileRef):
        msg = f"{who} takes a FileRef, such as fs.FsRef('data') / 'a.lock'; got {file!r}"
        raise TypeError(msg)
    return file


class Lock(Bracket):
    """Hold the exclusive lock on a file for the body's span.

    Args:
        file: the lock file, a ``FileRef``. Made with its parents when
            missing; it stays after release, naming its last holder.
        what: what the lock guards, as a refusal names it (``"indexer"``).
        wait: False to refuse a taken lock at once, True to wait for it,
            or a number of seconds to wait before refusing.
        body: the tree that runs while the lock is held. Leave it out to
            use the bracket inside a ``With``.

    Notes:
        - Taken, the file holds the holder's record as one JSON line,
          ``{host, pid, what, taken_at}``, which ``FsHeld`` and a refusal
          read back.
        - A POSIX lock belongs to the process, so a second take in the same
          process would quietly succeed. The paths this process holds are
          kept in a table, and a second take refuses as one from another
          process does. A waiting take in the same process waits for the
          first to release: with ``wait=True`` in one thread that never
          comes, so give a number.
        - Closing any descriptor on the file drops a POSIX lock, so read
          the lock file in this process through ``FsHeld`` only, never
          ``read_text``.
        - A process that dies frees its locks with it. On NFSv4 a holder
          on a machine that died frees it once its lease runs out.
        - A file system that cannot lock (``ENOLCK``, ``EOPNOTSUPP``) gives a
          ``FsLockWarning`` and runs the body unguarded.
        - A read only mount refuses with ``FsReadOnly``.

    Raises:
        FsLocked: another holder has the lock, and ``wait`` ran out or was
            off. Its ``holder`` is the holder's record.

    Example:
        index_lock = fs.FsRef("data") / "locks" / "index.lock"
        fs.Lock(index_lock, "indexer", body=reindex)
    """

    def __init__(
        self,
        file: FileRef,
        what: str | Nu = "",
        *,
        wait: bool | float | Nu = False,
        body: Nu | None = None,
    ) -> None:
        file = _file(file, "Lock")
        if not isinstance(wait, Nu):
            _check_wait(wait)
        # Children: [body, ref, p, what, wait].
        super().__init__(body, file.fs, file.p, what, wait)

    @contextmanager
    def _open(  # pyright: ignore[reportIncompatibleMethodOverride] - config named
        self, ctx: Context, ref: object, p: object, what: object, wait: object
    ) -> Iterator[None]:
        fabric = fabric_of(ref)
        deadline = _deadline(wait)
        while True:
            try:
                full, fd = fabric.lock(p, _what(what))
                break
            except FsLocked:
                if time.monotonic() >= deadline:
                    raise
            time.sleep(POLL)
        try:
            yield
        finally:
            fabric.unlock(full, fd)

    @asynccontextmanager
    async def _aopen(  # pyright: ignore[reportIncompatibleMethodOverride] - config named
        self, ctx: Context, ref: object, p: object, what: object, wait: object
    ) -> AsyncIterator[None]:
        fabric = fabric_of(ref)
        deadline = _deadline(wait)
        while True:
            try:
                full, fd = await _atake(fabric, p, _what(what))
                break
            except FsLocked:
                if time.monotonic() >= deadline:
                    raise
            await asyncio.sleep(POLL)
        try:
            yield
        finally:
            await asyncio.to_thread(fabric.unlock, full, fd)


class Hold(Bracket):
    """Write a file for the body's span, and remove it on the way out.

    For a file that says something holds while the body runs: a pid file,
    a claim, a ``ready`` marker.

    Args:
        file: the file, a ``FileRef``; missing parents are made.
        text: what to write in it.
        body: the tree that runs while the file is there.

    Notes:
        - The text is written whole on entry, as ``FsWriteText`` writes,
          replacing what was there.
        - On exit, raised or not, the file is removed only while it still
          holds exactly ``text`` (``FsRemoveIfHolds``), so a later holder's
          file is kept.
        - A read only mount refuses with ``FsReadOnly``.

    Example:
        owner = fs.FsRef("data") / "owner"
        fs.Hold(owner, "red 1234", body=serve)
    """

    def __init__(self, file: FileRef, text: str | Nu, *, body: Nu | None = None) -> None:
        file = _file(file, "Hold")
        # Children: [body, ref, p, text].
        super().__init__(body, file.fs, file.p, text)

    @contextmanager
    def _open(  # pyright: ignore[reportIncompatibleMethodOverride] - config named
        self, ctx: Context, ref: object, p: object, text: object
    ) -> Iterator[None]:
        fabric = fabric_of(ref)
        fabric.write(p, _text(text))
        try:
            yield
        finally:
            fabric.remove_if_holds(p, _text(text))

    @asynccontextmanager
    async def _aopen(  # pyright: ignore[reportIncompatibleMethodOverride] - config named
        self, ctx: Context, ref: object, p: object, text: object
    ) -> AsyncIterator[None]:
        fabric: FsFabric = fabric_of(ref)
        await asyncio.to_thread(fabric.write, p, _text(text))
        try:
            yield
        finally:
            await asyncio.to_thread(fabric.remove_if_holds, p, _text(text))


# --- helpers ----------------------------------------------------------------


def _check_wait(wait: object) -> None:
    """Refuse a ``wait`` that is no bool and no non-negative number of seconds."""
    if isinstance(wait, bool):
        return
    if not isinstance(wait, (int, float)) or wait < 0 or math.isnan(wait):
        raise ValueError(f"wait is True, False or seconds >= 0, got {wait!r}")


def _deadline(wait: object) -> float:
    """When a take stops trying: now for ``False``, never for ``True``."""
    _check_wait(wait)
    if wait is True:
        return math.inf
    if wait is False:
        return -math.inf
    return time.monotonic() + float(wait)  # type: ignore[arg-type]


async def _atake(fabric: FsFabric, p: object, what: str) -> tuple[str, int | None]:
    """``fabric.lock`` in a thread, released again when the take is cancelled.

    A cancelled ``to_thread`` leaves its thread running, so a lock it takes
    after the cancel would be held by nobody.
    """
    take = asyncio.ensure_future(asyncio.to_thread(fabric.lock, p, what))
    try:
        return await asyncio.shield(take)
    except asyncio.CancelledError:
        with contextlib.suppress(Exception):
            full, fd = await take
            await asyncio.to_thread(fabric.unlock, full, fd)
        raise


def _what(what: object) -> str:
    if not isinstance(what, str):
        raise TypeError(f"a lock's what is a str, got {what!r}")
    return what


def _text(text: object) -> str:
    if not isinstance(text, str):
        raise TypeError(f"Hold writes a str, got {type(text).__name__}")
    return text
