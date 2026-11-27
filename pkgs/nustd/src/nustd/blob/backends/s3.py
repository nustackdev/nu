"""Blobs as objects in an S3 bucket, one object per id."""

from __future__ import annotations

import asyncio
import io
import os
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, unquote

from .._base import (
    ThreadedBackend,
    _as_buffer,
    _pieces,
    _source_kind,
    _too_large,
    check_id,
    clamp,
    settled,
)
from ..protocol import BlobExists, BlobInfo, BlobNotFound


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable, Iterator

    from ..protocol import Source


__all__ = [
    "DEFAULT_PART_SIZE",
    "DEFAULT_READ_WINDOW",
    "GROW_EVERY",
    "MAX_METADATA",
    "MAX_OBJECT",
    "MAX_PARTS",
    "MAX_PART_SIZE",
    "MIN_PART_SIZE",
    "S3Backend",
]


MIN_PART_SIZE = 5 << 20
"""S3's smallest part, for every part of a multipart upload but the last."""

MAX_PART_SIZE = 5 << 30
"""S3's largest part, and its largest single PutObject."""

MAX_PARTS = 10_000
"""S3's most parts in one multipart upload."""

MAX_OBJECT = 5 << 40
"""S3's largest object, 5 TiB."""

MAX_METADATA = 2 << 10
"""S3's cap on an object's user metadata, 2 KiB: the UTF-8 bytes of every key and value."""

DEFAULT_PART_SIZE = 8 << 20
"""8 MiB, boto3's own multipart chunk size: the first part of a put of unknown size.

A put holds one part in memory.
"""

GROW_EVERY = 1000
"""Parts a put of unknown size sends at one size before doubling it.

From 8 MiB: 1,000 parts reach ~8 GiB, 5,000 ~250 GiB, and 10,000 pass S3's
5 TiB object cap, with parts of 4 GiB at most.
"""

DEFAULT_READ_WINDOW = 4
"""Ranged GETs one stream keeps in flight.

Measured on moto with 30 ms added to each GET, as a service's first byte
takes: 4 in flight read 1.3 to 1.4 times faster than 1, and reach 90% or more
of 16, for pieces of 4 to 16 MiB.
"""

_MISSING = frozenset({"404", "NoSuchKey", "NotFound"})
_RETRIES = 3
"""Tries of a conditional write that S3 answers with 409: a concurrent one on the key ran."""


class S3Backend(ThreadedBackend):
    """Blobs as objects: ``<prefix><id>`` in one bucket of any S3-compatible service.

    Write-once comes from the service: every write is conditional on
    ``If-None-Match: *`` (PutObject, and CompleteMultipartUpload), so a taken
    id is refused by S3 itself, across processes and machines, with no lock.
    An object shows up whole when its PutObject or CompleteMultipartUpload
    lands, never before, so a blob exists exactly while its object does.

    A put of a buffer up to ``part_size`` bytes is one PutObject. Anything
    bigger, and every file, path and iterable that runs past one part, goes
    up as a multipart upload, one part buffer at a time; a put that fails
    aborts its upload, so nothing is left a reader can find. A buffer or a
    path, whose size is known up front, goes in parts of
    ``max(part_size, ceil(size / 10000))``. A file or an iterable, whose size
    is not, starts at ``part_size`` and doubles it every ``GROW_EVERY``
    parts, up to S3's 5 GiB. A read is
    one ranged GetObject; a stream heads the object once, then sends one
    ranged GetObject per piece, each pinned to the object's ETag.

    The mime and name ride in the object's user metadata, percent-encoded
    (S3 metadata is ASCII only), with ``created_at``; the mime is also the
    object's ``Content-Type``. An object put by something else reads back
    with its ``Content-Type`` and ``LastModified`` instead.

    Limits, all native to S3:

    - One blob holds at most 5 TiB, S3's own cap, from any source. A stream
      of unknown size reaches it from a ``part_size`` of 6 MiB up; at 5 MiB
      its 10,000 growing parts top out at 4.88 TiB. A bigger put raises
      ``BlobTooLarge`` as soon as it passes the cap, and aborts what it sent.
    - Memory per running put is one part: ``part_size`` for most puts, more
      for a big one. A buffer costs none of its own (parts are slices of
      it); a path of size S holds ``max(part_size, S / 10000)``, 550 MB for
      a 5 TiB file; a stream holds its current part, which doubles past
      ~8 GiB sent (at the 8 MiB default) and reaches 4 GiB only near 5 TiB.
    - Write-once needs a service that honours ``If-None-Match`` on writes
      (AWS since 2024, R2, MinIO). One that ignores it lets a racing put of a
      taken id overwrite it; the pre-check still refuses a taken id that is
      not racing.
    - The mime and name share S3's 2 KiB of user metadata. Percent-encoded,
      an ASCII name can be about 1,900 characters, a Cyrillic one about 320
      (6 bytes each). A put over the cap raises ``ValueError`` before any
      request.
    - No open blobs (``supports_open`` is False): an object shows up whole
      and sealed when its put lands. ``put(seal=False)`` and ``append``
      raise ``NotImplementedError`` before any request; ``seal`` of a blob
      is a no-op, and a following read is a plain one.
    - ``delete`` is a HeadObject then a DeleteObject. S3's delete is
      idempotent (it succeeds on a missing key), so two racing deletes may
      both report a blob.
    - A multipart upload of a process that died mid-put is invisible but
      keeps its parts, billed, until aborted. Give the bucket a lifecycle
      rule that aborts incomplete multipart uploads after a day.
    - A stream is pinned to the ETag it saw at its first pull: a blob deleted,
      or deleted and put again under the same id, raises ``BlobNotFound``
      once the pieces read ahead of the change are pulled, within
      ``read_window`` pulls. A stream closed early leaves its GETs in flight
      to finish unread and sends no more.
    - S3 is strongly read-after-write consistent (AWS since 2020); a service
      that is not may miss a blob right after its put.
    - ``open`` builds the client and touches nothing: a missing bucket or bad
      credentials fail at the first call. The bucket must exist.
    - Without ``s3:ListBucket`` S3 answers a missing key with 403, which
      raises as boto3's ``ClientError``, not ``BlobNotFound``.
    - The async twins run the sync calls in a thread, as the local backends
      do. A cancelled ``aput`` waits for the request in flight, then aborts
      its upload; when that request was the last one, the blob has landed.

    Args:
        bucket: the bucket, made beforehand.
        prefix: put before every id to make its key, ``"space/"`` for
            ``space/<id>``. Nothing is added: end it with ``/`` for a folder.
        part_size: bytes of a multipart put's first part, at least 5 MiB, at
            most 5 GiB. A put that fits one part is one PutObject.
        read_window: ranged GETs a stream keeps in flight, 1 for one at a
            time.
        endpoint_url: the service, for anything that is not AWS (R2, MinIO).
        aws_access_key_id: with the secret and token, credentials for boto3;
            when all are left out boto3 finds them its usual way (env,
            profile, instance role).
    """

    supports_open = False
    """S3 holds no open blobs: an object is visible only once its put completes."""

    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "",
        part_size: int = DEFAULT_PART_SIZE,
        read_window: int = DEFAULT_READ_WINDOW,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        profile_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
    ) -> None:
        if not MIN_PART_SIZE <= part_size <= MAX_PART_SIZE:
            raise ValueError(
                f"part_size must be within [{MIN_PART_SIZE}, {MAX_PART_SIZE}], got {part_size}"
            )
        if read_window < 1:
            raise ValueError(f"read_window must be positive, got {read_window}")
        self.bucket = bucket
        self.prefix = prefix
        self.read_window = read_window
        self.part_size = part_size
        self.max_size = min(
            MAX_OBJECT,
            sum(_grown(part_size, n) for n in range(1, MAX_PARTS + 1, GROW_EVERY)) * GROW_EVERY,
        )
        self.endpoint_url = endpoint_url
        self._session_options = {
            "region_name": region_name,
            "profile_name": profile_name,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_session_token": aws_session_token,
        }
        self._client: Any = None
        self._error: type[Exception] = Exception

    def open(self) -> None:
        """Build the S3 client."""
        if self._client is not None:
            return
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as error:
            raise ImportError("S3Backend needs boto3: install nustd[blob_s3]") from error
        options = {key: value for key, value in self._session_options.items() if value is not None}
        # A session per backend: boto3 sessions are not thread safe, the
        # client they make is.
        session = boto3.session.Session(**options)
        self._client = session.client("s3", endpoint_url=self.endpoint_url)
        self._error = ClientError

    def close(self) -> None:
        """Close the client's connections."""
        client, self._client = self._client, None
        if client is not None:
            client.close()

    def _key(self, blob_id: str) -> str:
        return self.prefix + blob_id

    # ---- reads -------------------------------------------------------------------------------

    def _head(self, blob_id: str) -> dict[str, Any]:
        try:
            return self._client.head_object(Bucket=self.bucket, Key=self._key(blob_id))
        except self._error as error:
            if _code(error) in _MISSING:
                raise BlobNotFound(blob_id) from None
            raise

    def info(self, blob_id: str) -> BlobInfo:
        """What the blob is, apart from its bytes: one HeadObject."""
        check_id(blob_id)
        head = self._head(blob_id)
        meta = head.get("Metadata", {})
        created = meta.get("created-at")
        return BlobInfo(
            id=blob_id,
            size=int(head["ContentLength"]),
            mime=unquote(meta["mime"]) if "mime" in meta else head.get("ContentType", ""),
            name=unquote(meta.get("name", "")),
            created_at=float(created) if created else head["LastModified"].timestamp(),
        )

    def exists(self, blob_id: str) -> bool:
        """Whether the object is there: one HeadObject."""
        check_id(blob_id)
        try:
            self._head(blob_id)
        except BlobNotFound:
            return False
        return True

    def _read(self, blob_id: str, start: int, end: int | None) -> bytes:
        """The bytes of a range, in one ranged GetObject.

        S3 clamps the range's end itself; a start at or past the end answers
        416, read as empty. An empty range heads the object instead.
        """
        if end is not None and end <= start:
            self._head(blob_id)
            return b""
        options: dict[str, Any] = {}
        if start or end is not None:
            options["Range"] = f"bytes={start}-{'' if end is None else end - 1}"
        try:
            response = self._client.get_object(
                Bucket=self.bucket, Key=self._key(blob_id), **options
            )
        except self._error as error:
            if _code(error) in _MISSING:
                raise BlobNotFound(blob_id) from None
            if _code(error) == "InvalidRange":
                return b""
            raise
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def _pieces(self, blob_id: str, start: int, end: int | None, step: int) -> Iterator[bytes]:
        """The bytes of a range, ``step`` at a time, one ranged GetObject per piece.

        Up to ``read_window`` GETs run at once, each in a thread of the
        stream's own, and the pieces come out in order. A GET per piece
        rather than one GET read slowly: a stream pulled by a slow consumer
        (a browser seeking through a video) holds no connection between
        GETs, so it cannot starve the client's pool or be dropped idle by
        the service, and each piece is a short request that retries on its
        own. The price is one request per piece, and up to ``read_window``
        pieces read ahead, held in memory until pulled.
        """
        return self._stream_pieces(blob_id, start, end, step)

    def _get_range(self, blob_id: str, lo: int, hi: int, etag: str) -> bytes:
        """``[lo, hi)`` of the object, refused as gone unless it still has ``etag``."""
        try:
            response = self._client.get_object(
                Bucket=self.bucket,
                Key=self._key(blob_id),
                Range=f"bytes={lo}-{hi - 1}",
                IfMatch=etag,
            )
        except self._error as error:
            if _code(error) in _MISSING or _code(error) == "PreconditionFailed":
                raise BlobNotFound(blob_id) from None
            raise
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def _stream_pieces(
        self, blob_id: str, start: int, end: int | None, step: int
    ) -> Iterator[bytes]:
        head = self._head(blob_id)
        pos, stop = clamp(start, end, int(head["ContentLength"]))
        etag = head["ETag"]
        window = min(self.read_window, -(-(stop - pos) // step))
        if window <= 1:
            while pos < stop:
                piece = self._get_range(blob_id, pos, min(pos + step, stop), etag)
                if not piece:
                    return
                yield piece
                pos += len(piece)
            return
        pool = ThreadPoolExecutor(max_workers=window, thread_name_prefix="nustd-blob-s3")
        ahead: deque[Future[bytes]] = deque()
        try:
            while True:
                while len(ahead) < window and pos < stop:
                    upto = min(pos + step, stop)
                    ahead.append(pool.submit(self._get_range, blob_id, pos, upto, etag))
                    pos = upto
                if not ahead:
                    return
                piece = ahead.popleft().result()
                if not piece:
                    return
                yield piece
        finally:
            # Closed early: drop the GETs not begun; the ones running finish unread.
            pool.shutdown(wait=False, cancel_futures=True)

    def delete(self, blob_id: str) -> bool:
        """Remove the blob; whether there was one."""
        check_id(blob_id)
        found = self.exists(blob_id)
        if found:
            self._client.delete_object(Bucket=self.bucket, Key=self._key(blob_id))
        return found

    # ---- puts --------------------------------------------------------------------------------

    def put(
        self,
        source: Source,
        *,
        blob_id: str | None = None,
        mime: str = "",
        name: str = "",
        seal: bool = True,
    ) -> BlobInfo:
        """Store the bytes once under an id, sealed: visible whole when the put lands.

        Nothing spools to disk: a source past one part goes up a part at a
        time as it is read. ``seal=False`` raises ``NotImplementedError``.
        """
        _refuse_open(seal)
        kind = _source_kind(source)
        _check_metadata(mime, name)
        blob_id = self._claim(blob_id)
        info = BlobInfo(id=blob_id, size=0, mime=mime, name=name, created_at=time.time())
        if kind == "buffer":
            view = _as_buffer(source)  # type: ignore[arg-type]
            self._check_size(view.nbytes)
            return self._send(info, _slices(view, self._known(view.nbytes)))
        if kind == "path":
            path = Path(source)  # type: ignore[arg-type]
            with path.open("rb") as file:
                size = os.fstat(file.fileno()).st_size
                self._check_size(size)
                fixed = self._known(size)
                parts = _parts(_pieces(file), lambda _: fixed, self.max_size)
                return self._send(info, parts)
        return self._send(info, _parts(_pieces(source), self._growing, self.max_size))

    async def _aput_iterable(
        self,
        source: AsyncIterable[bytes],
        blob_id: str | None,
        mime: str,
        name: str,
        seal: bool,
    ) -> BlobInfo:
        """Send each part off the event loop as soon as the iterable fills it."""
        _refuse_open(seal)
        _check_metadata(mime, name)
        blob_id = await asyncio.to_thread(self._claim, blob_id)
        info = BlobInfo(id=blob_id, size=0, mime=mime, name=name, created_at=time.time())
        upload = _Upload(self, info)
        try:
            async for view, last in _aparts(source, self._growing, self.max_size):
                await settled(asyncio.to_thread(upload.send, view, last))
        except BaseException:
            await asyncio.to_thread(upload.abort)
            raise
        return upload.info

    def append(self, blob_id: str, source: Source) -> BlobInfo:
        """Refused: S3 holds no open blobs, so ``NotImplementedError``."""
        raise NotImplementedError(_NO_OPEN)

    async def _aappend_iterable(self, blob_id: str, source: AsyncIterable[bytes]) -> BlobInfo:
        """Refused: S3 holds no open blobs, so ``NotImplementedError``."""
        raise NotImplementedError(_NO_OPEN)

    def seal(self, blob_id: str) -> BlobInfo:
        """Every S3 blob is sealed: a no-op that heads the object (``BlobNotFound`` when missing)."""
        return self.info(blob_id)

    def _known(self, size: int) -> int:
        """The part size of a put whose size is known: 10,000 parts cover it."""
        return max(self.part_size, -(-size // MAX_PARTS))

    def _growing(self, number: int) -> int:
        """The size of part ``number`` (from 1) of a put whose size is not known."""
        return _grown(self.part_size, number)

    def _check_size(self, size: int) -> None:
        error = _too_large(size, self.max_size)
        if error is not None:
            raise error

    def _send(self, info: BlobInfo, parts: Iterator[tuple[memoryview, bool]]) -> BlobInfo:
        upload = _Upload(self, info)
        try:
            for view, last in parts:
                upload.send(view, last)
        except BaseException:
            upload.abort()
            raise
        return upload.info

    def _conditional(self, call: Any, blob_id: str, **options: Any) -> dict[str, Any]:  # noqa: ANN401
        """A write conditional on the key being free; a taken key raises ``BlobExists``."""
        body = options.get("Body")
        for attempt in range(_RETRIES):
            # A try that S3 refused may have read the body already.
            if body is not None:
                body.seek(0)
            try:
                return call(Bucket=self.bucket, IfNoneMatch="*", **options)
            except self._error as error:
                code = _code(error)
                if code == "PreconditionFailed":
                    raise BlobExists(blob_id) from None
                if code != "ConditionalRequestConflict" or attempt == _RETRIES - 1:
                    raise
            time.sleep(0.05 * (attempt + 1))
        raise AssertionError("unreachable")  # pragma: no cover


class _Upload:
    """One put's trip to S3: a single PutObject when the first part is the last, else multipart."""

    def __init__(self, backend: S3Backend, info: BlobInfo) -> None:
        self._backend = backend
        self.info = info
        self._key = backend._key(info.id)
        self._upload_id: str | None = None
        self._parts: list[dict[str, Any]] = []
        self._size = 0

    def _extra(self) -> dict[str, Any]:
        extra: dict[str, Any] = {
            "Metadata": _metadata(self.info.mime, self.info.name, self.info.created_at)
        }
        if self.info.mime and self.info.mime.isascii() and self.info.mime.isprintable():
            extra["ContentType"] = self.info.mime
        return extra

    def send(self, view: memoryview, last: bool) -> None:
        """Send the next part; the last one completes the blob."""
        backend, client = self._backend, self._backend._client
        self._size += view.nbytes
        if self._upload_id is None and last:
            backend._conditional(
                client.put_object,
                self.info.id,
                Key=self._key,
                Body=_ViewReader(view),
                **self._extra(),
            )
        else:
            if self._upload_id is None:
                response = client.create_multipart_upload(
                    Bucket=backend.bucket, Key=self._key, **self._extra()
                )
                self._upload_id = response["UploadId"]
            number = len(self._parts) + 1
            response = client.upload_part(
                Bucket=backend.bucket,
                Key=self._key,
                UploadId=self._upload_id,
                PartNumber=number,
                Body=_ViewReader(view),
            )
            self._parts.append({"ETag": response["ETag"], "PartNumber": number})
            if last:
                backend._conditional(
                    client.complete_multipart_upload,
                    self.info.id,
                    Key=self._key,
                    UploadId=self._upload_id,
                    MultipartUpload={"Parts": self._parts},
                )
        if last:
            self.info = BlobInfo(
                id=self.info.id,
                size=self._size,
                mime=self.info.mime,
                name=self.info.name,
                created_at=self.info.created_at,
            )
            self._upload_id = None

    def abort(self) -> None:
        """Drop the parts sent so far; a put that never got past one part has none."""
        if self._upload_id is None:
            return
        upload_id, self._upload_id = self._upload_id, None
        self._backend._client.abort_multipart_upload(
            Bucket=self._backend.bucket, Key=self._key, UploadId=upload_id
        )


class _ViewReader(io.RawIOBase):
    """A seekable binary file over a memoryview, so botocore reads a part without copying it."""

    def __init__(self, view: memoryview) -> None:
        self._view = view
        self._pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:  # noqa: ANN401 (a writable buffer)
        size = min(len(buffer), self._view.nbytes - self._pos)
        buffer[:size] = self._view[self._pos : self._pos + size]
        self._pos += size
        return size

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._pos, io.SEEK_END: self._view.nbytes}[whence]
        self._pos = max(0, base + offset)
        return self._pos

    def tell(self) -> int:
        return self._pos

    def __len__(self) -> int:
        return self._view.nbytes


def _slices(view: memoryview, size: int) -> Iterator[tuple[memoryview, bool]]:
    """A buffer as parts of ``size``, each a slice of it, no copy."""
    if view.nbytes <= size:
        yield view, True
        return
    for offset in range(0, view.nbytes, size):
        yield view[offset : offset + size], offset + size >= view.nbytes


class _Filler:
    """A part buffer, filled from pieces and handed out as a part when full.

    A full buffer goes out only once a further byte arrives, so the part
    known to be the last is flagged. The buffer is reused while the part
    size holds, and replaced when the schedule grows it.
    """

    def __init__(self, schedule: Callable[[int], int], limit: int | None) -> None:
        self._schedule = schedule
        self._number = 1
        self._buffer = bytearray(schedule(1))
        self._filled = 0
        self._total = 0
        self._limit = limit

    def feed(self, piece: object) -> Iterator[memoryview]:
        """The full parts the piece completes, before its rest goes in."""
        view = memoryview(piece).cast("B")  # type: ignore[arg-type]
        self._total += view.nbytes
        error = _too_large(self._total, self._limit)
        if error is not None:
            raise error
        while view.nbytes:
            if self._filled == len(self._buffer):
                yield memoryview(self._buffer)
                self._number += 1
                size = self._schedule(self._number)
                if size != len(self._buffer):
                    self._buffer = bytearray(size)
                self._filled = 0
            take = min(len(self._buffer) - self._filled, view.nbytes)
            self._buffer[self._filled : self._filled + take] = view[:take]
            self._filled += take
            view = view[take:]

    def rest(self) -> memoryview:
        """The last part."""
        return memoryview(self._buffer)[: self._filled]


def _parts(
    pieces: Iterable[object], schedule: Callable[[int], int], limit: int | None
) -> Iterator[tuple[memoryview, bool]]:
    filler = _Filler(schedule, limit)
    for piece in pieces:
        for part in filler.feed(piece):
            yield part, False
    yield filler.rest(), True


async def _aparts(
    pieces: AsyncIterable[object], schedule: Callable[[int], int], limit: int | None
) -> AsyncIterator[tuple[memoryview, bool]]:
    filler = _Filler(schedule, limit)
    async for piece in pieces:
        for part in filler.feed(piece):
            yield part, False
    yield filler.rest(), True


_NO_OPEN = (
    "S3Backend holds no open blobs: an object is visible only once its put completes, "
    "so seal=False and append are not supported; put the bytes whole, or use the lmdb or "
    "files backend for a blob read while it is written"
)


def _refuse_open(seal: bool) -> None:
    if not seal:
        raise NotImplementedError(_NO_OPEN)


def _grown(part_size: int, number: int) -> int:
    """Part ``number`` (from 1) of a put of unknown size: doubled every ``GROW_EVERY``, 5 GiB at most."""
    return min(part_size << ((number - 1) // GROW_EVERY), MAX_PART_SIZE)


def _metadata(mime: str, name: str, created_at: float) -> dict[str, str]:
    """The object's user metadata: S3 takes ASCII only, so mime and name go percent-encoded."""
    return {
        "mime": quote(mime, safe=""),
        "name": quote(name, safe=""),
        "created-at": repr(created_at),
    }


def _check_metadata(mime: str, name: str) -> None:
    """Refuse a mime and name whose metadata S3 would refuse, before any request."""
    size = sum(len(k) + len(v) for k, v in _metadata(mime, name, time.time()).items())
    if size > MAX_METADATA:
        raise ValueError(
            f"mime and name take {size} bytes of S3 metadata, the cap is {MAX_METADATA}"
        )


def _code(error: Exception) -> str:
    return str(getattr(error, "response", {}).get("Error", {}).get("Code", ""))
