"""What a blob backend is: append-only bytes under an id, read whole, by range or as they grow."""

from __future__ import annotations

import os
from collections.abc import AsyncIterable, Iterable
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, BinaryIO, Protocol, Union, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Mapping


__all__ = [
    "STEP",
    "AsyncSource",
    "BlobBackend",
    "BlobExists",
    "BlobIdle",
    "BlobInfo",
    "BlobNotFound",
    "BlobSealed",
    "BlobTooLarge",
    "Source",
]


STEP = 1 << 20
"""Bytes per piece a stream yields unless told otherwise."""

Source = Union[bytes, bytearray, memoryview, os.PathLike, BinaryIO, Iterable[bytes]]  # noqa: UP007
"""What a put takes.

A path is an ``os.PathLike``; a ``str`` is refused as ambiguous.
"""

AsyncSource = Union[Source, AsyncIterable[bytes]]  # noqa: UP007


@dataclass(frozen=True)
class BlobInfo:
    """What a blob is, apart from its bytes.

    ``size`` is the bytes committed so far: final once ``sealed``, growing
    before. A record written before blobs could be open reads as sealed.
    """

    id: str
    size: int
    mime: str = ""
    name: str = ""
    created_at: float = 0.0
    sealed: bool = True

    def to_dict(self) -> dict[str, object]:
        """Plain dict, for a meta record or the wire."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BlobInfo:
        """Read back what ``to_dict`` wrote."""
        return cls(
            id=str(data["id"]),
            size=int(data["size"]),  # type: ignore[arg-type]
            mime=str(data.get("mime", "")),
            name=str(data.get("name", "")),
            created_at=float(data.get("created_at", 0.0)),  # type: ignore[arg-type]
            sealed=bool(data.get("sealed", True)),
        )


class BlobNotFound(LookupError):  # noqa: N818 - a state, not an error kind
    """No blob under this id."""


class BlobExists(LookupError):  # noqa: N818 - a state, not an error kind
    """A blob already sits under this id.

    A put takes a fresh id: an open blob grows by ``append``, and a change to
    a sealed one is a new id.
    """


class BlobSealed(ValueError):  # noqa: N818 - a state, not an error kind
    """The blob is sealed: no more bytes may be appended to it."""


class BlobIdle(Exception):  # noqa: N818 - a state, not an error kind
    """A following read waited its ``idle`` seconds and the open blob did not grow.

    Its writer may be gone: anyone may ``seal`` an abandoned blob. Not a
    ``TimeoutError``: that is an ``OSError``, which a server reads as the
    client gone.
    """


class BlobTooLarge(ValueError):  # noqa: N818 - a state, not an error kind
    """The backend cannot hold one blob this big.

    S3 caps an object at 5 TiB; a backend's ``max_size``, when set, caps it lower.
    """


@runtime_checkable
class BlobBackend(Protocol):
    """Append-only bytes under an id: put, append and seal; read whole, by range or following.

    A blob is readable from its first committed bytes and never rewritten:
    it only grows, until ``sealed`` says no more bytes will come. A plain put
    seals itself when its source ends. A put with ``seal=False`` leaves the
    blob open, to grow by ``append`` and close by ``seal``, once.

    A put that fails deletes what it wrote, so it leaves nothing a reader can
    find (a follower gets ``BlobNotFound``). An append that fails leaves the
    blob open with the bytes it committed. One writer at a time per blob: a
    second append, or a seal, waits for the one in flight.

    Ranges are half-open, ``[start, end)``, and clamp to the blob's size, so
    a range past the end reads short or empty; a negative bound is a
    ``ValueError``. A following read (``follow=True``) waits for bytes past
    the current end instead, until the blob is sealed.

    An id is 32 lowercase hex characters, the shape of ``uuid4().hex``. Every
    call refuses any other id with ``ValueError`` before touching the store, so
    an id can never name a path outside it.
    """

    supports_open: bool
    """Whether the backend holds open blobs: ``seal=False``, ``append``, a following read that waits.

    False for s3, where a blob shows up whole and sealed when its put lands.
    """

    def open(self) -> None:
        """Open the store.

        Every other call needs it open.
        """
        ...

    def close(self) -> None:
        """Close the store."""
        ...

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
        seal: bool = True,
    ) -> BlobInfo:
        """Store the bytes under a fresh id, readable as they commit.

        Never holds an iterable or a file whole in memory.

        Args:
            source: a ``str`` is refused with ``TypeError``: text or a path is
                ambiguous, pass bytes or a ``Path``.
            blob_id: the id to store under, minted when None. Pass one minted
                outside a retried block so a retry finds ``BlobExists`` rather
                than leaving a second copy behind.
            mime: the media type a reader serves the bytes as; stored, not checked.
            name: the file name a download offers; stored, not checked.
            seal: seal the blob when the source ends. False leaves it open
                for ``append``; ``put(b"", seal=False)`` makes an empty open
                blob. A backend that holds no open blobs raises
                ``NotImplementedError``.
        """
        ...

    def append(self, blob_id: str, source: Source) -> BlobInfo:
        """Add the bytes to the end of an open blob.

        Raises ``BlobNotFound`` when no blob sits under the id, ``BlobSealed``
        when it is sealed.
        """
        ...

    def seal(self, blob_id: str) -> BlobInfo:
        """Close the blob: no more bytes will come.

        Sealing a sealed blob is a no-op. Raises ``BlobNotFound`` when no
        blob sits under the id.
        """
        ...

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes.

        Raises ``BlobNotFound`` when no blob sits under the id.
        """
        ...

    def exists(self, blob_id: str) -> bool:
        """Whether a blob sits under the id, open or sealed."""
        ...

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, in one piece.

        On an open blob it waits, as a following stream does: for the seal,
        or for the bytes up to ``end``. A big range sits whole in memory: use
        ``stream`` for those.
        """
        ...

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
        """The bytes of a range, ``step`` at a time.

        A missing blob raises ``BlobNotFound`` at the first pull, not at the call.

        Args:
            blob_id: the blob's id.
            start: the first byte, from 0.
            end: one past the last byte; None for the end of the blob.
            step: bytes per piece; the last piece may be shorter.
            follow: on an open blob, read to the current end and then wait
                for more until it is sealed; an ``end`` past the current size
                waits for those bytes. On a sealed blob it is a plain read.
                A blob deleted while followed raises ``BlobNotFound``.
            idle: seconds a following read waits with no growth before
                ``BlobIdle``; None waits for ever.
        """
        ...

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one."""
        ...

    async def aput(
        self,
        source: AsyncSource,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
        seal: bool = True,
    ) -> BlobInfo:
        """``put``, off the event loop.

        Also takes an async iterable of bytes.
        """
        ...

    async def aappend(self, blob_id: str, source: AsyncSource) -> BlobInfo:
        """``append``, off the event loop; also takes an async iterable of bytes."""
        ...

    async def aseal(self, blob_id: str) -> BlobInfo:
        """``seal``, off the event loop."""
        ...

    async def ainfo(self, blob_id: str) -> BlobInfo:
        """``info``, off the event loop."""
        ...

    async def aexists(self, blob_id: str) -> bool:
        """``exists``, off the event loop."""
        ...

    async def aread(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """``read``, off the event loop."""
        ...

    def astream(
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
        ...

    async def adelete(self, blob_id: str) -> bool:
        """``delete``, off the event loop."""
        ...
