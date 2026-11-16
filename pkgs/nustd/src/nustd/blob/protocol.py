"""What a blob backend is: write-once bytes under an id, read whole or by range."""

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
    "BlobInfo",
    "BlobNotFound",
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
    """What a blob is, apart from its bytes."""

    id: str
    size: int
    mime: str = ""
    name: str = ""
    created_at: float = 0.0

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
        )


class BlobNotFound(LookupError):  # noqa: N818 - a state, not an error kind
    """No blob under this id."""


class BlobExists(LookupError):  # noqa: N818 - a state, not an error kind
    """A blob already sits under this id.

    Blobs are write-once: a change is a new id.
    """


class BlobTooLarge(ValueError):  # noqa: N818 - a state, not an error kind
    """The backend cannot hold one value this big.

    LMDB caps a value near 4 GiB.
    """


@runtime_checkable
class BlobBackend(Protocol):
    """Write-once bytes under an id: put once, read whole or by range, sync and async.

    A blob is visible whole or not at all: a put that dies halfway leaves
    nothing a reader can find. Ranges are half-open, ``[start, end)``, and
    clamp to the blob's size, so a range past the end reads short or empty;
    a negative bound is a ``ValueError``.

    An id is 32 lowercase hex characters, the shape of ``uuid4().hex``. Every
    call refuses any other id with ``ValueError`` before touching the store, so
    an id can never name a path outside it.
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
    ) -> BlobInfo:
        """Store the bytes once under an id.

        Never holds an iterable or a file whole in memory.

        Args:
            source: a ``str`` is refused with ``TypeError``: text or a path is
                ambiguous, pass bytes or a ``Path``.
            blob_id: the id to store under, minted when None. Pass one minted
                outside a retried block so a retry finds ``BlobExists`` rather
                than leaving a second copy behind.
            mime: the media type a reader serves the bytes as; stored, not checked.
            name: the file name a download offers; stored, not checked.
        """
        ...

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes.

        Raises ``BlobNotFound`` when no blob sits under the id.
        """
        ...

    def exists(self, blob_id: str) -> bool:
        """Whether a whole blob sits under the id."""
        ...

    def read(self, blob_id: str, start: int = 0, end: int | None = None) -> bytes:
        """The bytes of a range, in one piece.

        A big range sits whole in memory: use ``stream`` for those.
        """
        ...

    def stream(
        self,
        blob_id: str,
        start: int = 0,
        end: int | None = None,
        *,
        step: int = STEP,
    ) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time.

        A missing blob raises ``BlobNotFound`` at the first pull, not at the call.
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
    ) -> BlobInfo:
        """``put``, off the event loop.

        Also takes an async iterable of bytes.
        """
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
    ) -> AsyncIterator[bytes]:
        """``stream``, each piece read off the event loop."""
        ...

    async def adelete(self, blob_id: str) -> bool:
        """``delete``, off the event loop."""
        ...
