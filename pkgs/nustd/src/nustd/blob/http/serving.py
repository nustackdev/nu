"""Blob stores over http: the routes a mount serves, and the backend held open behind them.

Plain Starlette over plain backends: a request reads the backend directly,
no tree runs. Needs Starlette, which comes with ``nustd[ws_server]``.

``serve_blobs`` is the usual entry: for each mount and the backend of the
store it serves, the routes and the bracket holding the backend open. Put the
brackets around the server in a ``nu.With`` and hand it the routes;
``nustd.ui.serve(blobs=...)`` does both.

The server runs outside any tree, so it takes plain Python: a backend
(``nustd.blob.LMDBBackend``, ``FilesBackend``, ``S3Backend``), not the spec a
tree binds (``nustd.blob.lmdb``, ``files``, ``s3``). A program that both
serves a store and runs trees on it writes the config twice, once for each;
the same path or bucket is the same store, and an LMDB env opened twice in
one process is one env, shared.
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urlsplit

from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from nu.context.fabric import Fabric, Provide
from nustd.blob import STEP, BlobBackend, BlobNotFound, BlobTooLarge
from nustd.blob._base import check_id

from . import BlobMount


if TYPE_CHECKING:
    from collections.abc import AsyncIterable, AsyncIterator, Mapping

    from starlette.requests import Request

    from nu.lang.runtime import Context
    from nustd.blob import BlobInfo


__all__ = [
    "CACHE_CONTROL",
    "MAX_FIELD",
    "NAME_HEADER",
    "HeldOpen",
    "routes",
    "same_origin",
    "serve_blobs",
]


CACHE_CONTROL = "public, max-age=31536000, immutable"
"""Every blob is write-once under its id, so a url never changes what it serves."""

NAME_HEADER = "X-Blob-Name"
"""The upload header naming the file, percent-encoded UTF-8 (``encodeURIComponent``)."""

_FALLBACK_MIME = "application/octet-stream"

MAX_FIELD = 1 << 10
"""The most characters an upload's mime or name may hold.

A backend keeps both beside the bytes, and s3 has only 2 KiB of metadata for
the two together; a bound here answers 400 before any backend is asked.
"""

_SPEC = re.compile(r"(\d*)-(\d*)", re.ASCII)

_HEADER_SAFE = re.compile(r"[ -~]*")

_HUGE = 1 << 64
"""Stands in for a range bound too long to parse: past any blob's end."""


class _NotSatisfiable(Exception):  # noqa: N818 - a state, not an error kind
    """The range starts past the blob's end."""


class _UploadTooLarge(Exception):  # noqa: N818 - a state, not an error kind
    """The upload passed the routes' size cap."""


def serve_blobs(blobs: Mapping[BlobMount, BlobBackend]) -> tuple[list[Provide], list[Route]]:
    """The routes for each mount, over its backend, and the brackets holding each backend open.

    Put every bracket before the server in a ``nu.With``, so each store is
    open while the server answers, and hand the server the routes. A tree
    that reaches the same store binds its own spec with the same config
    (``nu.With(nustd.blob.lmdb(Files, path), ...)``): the same path or bucket
    is the same store.

    Args:
        blobs: each mount, to the backend of the store it serves, not open
            yet: a ``nustd.blob.LMDBBackend``, ``FilesBackend`` or
            ``S3Backend``, or any ``BlobBackend``. One backend may sit under
            several mounts (say, each with its own upload rules); it gets one
            bracket, so it opens and closes once.

    Returns:
        ``(brackets, routes)``.

    Raises:
        TypeError: a key is no ``BlobMount``, or a value is no backend, such
            as the spec a tree binds.
        ValueError: two mounts sit at one path.

    Example:
        files = nustd.blob.http.BlobMount("/files")
        brackets, served = serve_blobs({files: nustd.blob.LMDBBackend(".store/files")})
        nu.With(*brackets, nustd.ws_server.listen(..., routes=served), body=...)
    """
    brackets: list[Provide] = []
    served: list[Route] = []
    seen: set[str] = set()
    held: set[int] = set()
    for mount, backend in blobs.items():
        if not isinstance(mount, BlobMount):
            raise TypeError(f"a blob mount is a nustd.blob.http.BlobMount, got {mount!r}")
        if mount.at in seen:
            raise ValueError(f"two stores mounted at {mount.at!r}")
        seen.add(mount.at)
        # A class has the protocol's methods too, so it would pass the check.
        if isinstance(backend, type) or not isinstance(backend, BlobBackend):
            raise TypeError(_no_backend(mount, backend))
        if id(backend) not in held:
            held.add(id(backend))
            brackets.append(Provide(HeldOpen, kwargs={"backend": backend}))
        served += routes(mount, backend)
    return brackets, served


def _no_backend(mount: BlobMount, value: object) -> str:
    """Why ``value`` cannot serve ``mount``, with what to pass instead."""
    hint = (
        "the server takes a backend, such as nustd.blob.LMDBBackend(path); "
        "the spec (nustd.blob.lmdb, files, s3) is what a tree binds"
    )
    if isinstance(value, Provide):
        return f"{mount!r} got a tree's spec: {hint}"
    return f"{mount!r} needs a blob backend, got {value!r}: {hint}"


class HeldOpen(Fabric):
    """A blob backend open for the span of its bracket: what a mount's routes read.

    The routes are built with the backend before any bracket runs, so this
    opens the instance they hold rather than making one.

    Args:
        backend: the backend the routes serve, not open yet.
    """

    def __init__(self, backend: BlobBackend) -> None:
        self.backend = backend

    def setup(self, ctx: Context) -> None:
        """Open the backend."""
        self.backend.open()

    def cleanup(self) -> None:
        """Close the backend."""
        self.backend.close()

    async def asetup(self, ctx: Context) -> None:
        """Open the backend off the loop: a first open may make the store's files."""
        await asyncio.to_thread(self.backend.open)

    async def acleanup(self) -> None:
        """Close the backend off the loop."""
        await asyncio.to_thread(self.backend.close)


def routes(mount: BlobMount, backend: BlobBackend, *, step: int = STEP) -> list[Route]:
    """Starlette routes serving one store's blobs at ``mount`` and taking uploads into it.

    A blob is at ``{at}/<id>``; an upload POSTs to ``{at}``. The backend is
    opened and closed by the caller (``HeldOpen``), not here.

    GET streams the blob, shown in place (``inline``), or saved with
    ``?download=1`` (``attachment``): 200 whole, 206 for one ``Range`` (``bytes=a-b``,
    ``bytes=a-`` or ``bytes=-n``), 416 when it starts past the end, 304 when
    ``If-None-Match`` holds the id. A ``Range`` with several ranges, one that
    does not parse, or one on an empty blob is ignored and the blob comes
    whole, as RFC 9110 allows; so is a ``Range`` whose ``If-Range`` is not the
    blob's ETag (a date never matches: no ``Last-Modified`` is sent). HEAD
    gives GET's headers and reads no bytes; it ignores ``Range``, as RFC 9110
    asks. A malformed id or a missing blob is a 404.

    POST takes the raw body as the blob (a multipart form is stored as is,
    not parsed), streamed into the backend as it arrives. The ``Content-Type``
    is stored whole, parameters included, so a ``charset`` comes back on GET.
    The name comes from ``X-Blob-Name`` or else ``?name=``. Answers 201 with
    ``{id, size, mime, name}`` and the blob's url in ``Location`` (under the
    app's ``root_path``, so it holds under a ``Mount`` or a proxy). A mime or
    name over ``MAX_FIELD`` characters, or one the backend refuses before
    reading the body (s3's metadata cap), is a 400 and stores nothing. One
    over the mount's ``max_upload`` is a 413: refused before reading when its
    ``Content-Length`` says so, cut off at the first byte past the cap
    otherwise. One a browser sent from another site is a 403, unless the
    mount takes ``cross_site`` uploads (``same_origin``).

    Args:
        mount: where the store sits, and its upload rules.
        backend: the store's backend, open while the routes answer.
        step: bytes per piece a GET reads and sends.
    """
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")
    at = mount.at
    max_upload = mount.max_upload

    async def serve(request: Request) -> Response:
        blob_id = request.path_params["blob_id"]
        if not _is_id(blob_id):
            return _not_found()
        try:
            info = await backend.ainfo(blob_id)
        except BlobNotFound:
            return _not_found()
        etag = f'"{info.id}"'
        if _none_match(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers={"etag": etag, "cache-control": CACHE_CONTROL})
        headers = _headers(info, etag, attachment=_wants_download(request))
        if request.method == "HEAD":
            return Response(headers={**headers, "content-length": str(info.size)})
        span = None
        if request.headers.get("if-range", etag).strip() == etag:
            try:
                span = _byte_range(request.headers.get("range"), info.size)
            except _NotSatisfiable:
                return Response(
                    status_code=416,
                    headers={"content-range": f"bytes */{info.size}", "accept-ranges": "bytes"},
                )
        start, end = span or (0, info.size)
        if span is not None:
            headers["content-range"] = f"bytes {start}-{end - 1}/{info.size}"
        headers["content-length"] = str(end - start)
        pieces = backend.astream(blob_id, start, end, step=step)
        try:
            # Pulled before answering, so a blob deleted since ``ainfo`` is a 404,
            # not a 200 that breaks off after its headers.
            first = await pieces.__anext__()
        except StopAsyncIteration:
            first = b""
        except BlobNotFound:
            return _not_found()
        return StreamingResponse(
            _chain(first, pieces),
            status_code=200 if span is None else 206,
            headers=headers,
        )

    async def upload(request: Request) -> Response:
        if not mount.cross_site and not same_origin(request):
            return Response("cross-site upload refused", status_code=403, media_type="text/plain")
        declared = request.headers.get("content-length", "")
        if max_upload is not None and declared.isascii() and declared.isdigit():
            if _bound(declared) > max_upload:
                return _too_large()
        mime = request.headers.get("content-type", "").strip()
        name = request.headers.get(NAME_HEADER)
        name = unquote(name) if name is not None else request.query_params.get("name", "")
        if len(mime) > MAX_FIELD or len(name) > MAX_FIELD:
            return _bad_request(f"mime and name hold at most {MAX_FIELD} characters each")
        body = _Body(request.stream(), max_upload)
        try:
            info = await backend.aput(body.pieces(), mime=mime, name=name)
        except (_UploadTooLarge, BlobTooLarge):
            return _too_large()
        except ClientDisconnect:
            # The backend dropped the partial put; the client is gone, so this never arrives.
            return Response(status_code=400)
        except ValueError as exc:
            # Refused before a byte was read: the request's fault (s3's metadata
            # cap). Once the body is flowing, a ValueError is the server's.
            if body.started:
                raise
            return _bad_request(str(exc))
        root = request.scope.get("root_path", "")
        return JSONResponse(
            {"id": info.id, "size": info.size, "mime": info.mime, "name": info.name},
            status_code=201,
            headers={"location": f"{root}{at}/{info.id}"},
        )

    return [
        Route(f"{at}/{{blob_id}}", serve, methods=["GET", "HEAD"]),
        Route(at, upload, methods=["POST"]),
    ]


_OWN_SITES = frozenset({"same-origin", "none"})
"""The ``Sec-Fetch-Site`` values of a request the page itself made, or the user typed."""


def same_origin(request: Request) -> bool:
    """Whether ``request`` came from this server's own page, or from no page at all.

    A browser's ``Sec-Fetch-Site`` decides when it is sent: ``same-origin``
    or ``none`` passes. It holds behind a dev server's proxy, where the
    browser's origin is the proxy's. Without it, an ``Origin`` must name the
    request's ``Host``. A request with neither (curl, a script) passes: it
    is no browser acting for a page.
    """
    site = request.headers.get("sec-fetch-site")
    if site is not None:
        return site in _OWN_SITES
    origin = request.headers.get("origin")
    if origin is None:
        return True
    return urlsplit(origin).netloc == request.headers.get("host", "")


def _is_id(blob_id: str) -> bool:
    try:
        check_id(blob_id)
    except ValueError:
        return False
    return True


def _not_found() -> Response:
    return Response("blob not found", status_code=404, media_type="text/plain")


def _bad_request(reason: str) -> Response:
    return Response(reason, status_code=400, media_type="text/plain")


def _too_large() -> Response:
    return Response("upload too large", status_code=413, media_type="text/plain")


def _wants_download(request: Request) -> bool:
    """Whether the url asks to save the blob rather than show it: ``?download=1``."""
    return request.query_params.get("download", "") not in ("", "0", "false")


def _headers(info: BlobInfo, etag: str, *, attachment: bool = False) -> dict[str, str]:
    """What a GET and a HEAD of the blob both carry, length aside."""
    headers = {
        "etag": etag,
        "cache-control": CACHE_CONTROL,
        "accept-ranges": "bytes",
        "content-type": _content_type(info.mime),
        "x-content-type-options": "nosniff",
    }
    disposition = _disposition(info.name, attachment=attachment)
    if disposition is not None:
        headers["content-disposition"] = disposition
    return headers


def _content_type(mime: str) -> str:
    """The stored mime, or the generic one when it is empty or unsafe in a header.

    A mime put through a backend directly is not checked, so it may hold a
    line break or a non-ascii character that would break the response.
    """
    if mime and _HEADER_SAFE.fullmatch(mime):
        return mime
    return _FALLBACK_MIME


def _disposition(name: str, *, attachment: bool = False) -> str | None:
    """``inline`` (or ``attachment``) with the stored name: ``filename`` in ascii, plus ``filename*`` (RFC 6266) when it differs.

    An attachment with no name still says so, and the browser picks the name.
    """
    name = "".join(char for char in name if char.isprintable())
    kind = "attachment" if attachment else "inline"
    if not name:
        return kind if attachment else None
    fallback = "".join(char if " " <= char <= "~" and char not in '"\\' else "_" for char in name)
    value = f'{kind}; filename="{fallback}"'
    if fallback != name:
        value += f"; filename*=UTF-8''{quote(name.encode('utf-8', 'replace'), safe='')}"
    return value


def _none_match(header: str | None, etag: str) -> bool:
    """Whether ``If-None-Match`` names the blob.

    The comparison is weak, as RFC 9110 asks: ``W/"<id>"`` matches too.
    """
    if header is None:
        return False
    return any(tag.strip() in ("*", etag, f"W/{etag}") for tag in header.split(","))


def _bound(digits: str) -> int:
    digits = digits.lstrip("0") or "0"
    return int(digits) if len(digits) <= 19 else _HUGE


def _byte_range(header: str | None, size: int) -> tuple[int, int] | None:
    """The half-open range one ``bytes=`` spec asks for, cut to the size.

    None serves the blob whole. Raises ``_NotSatisfiable`` when the range starts at or past the end, or
    is an empty suffix (``bytes=-0``).
    """
    if header is None or size == 0:
        return None
    unit, _, spec = header.partition("=")
    if unit.strip().lower() != "bytes":
        return None
    match = _SPEC.fullmatch(spec.strip())
    if match is None:
        return None  # several ranges, or not a range at all
    first, last = match.groups()
    if not first:
        if not last:
            return None
        length = _bound(last)
        if length == 0:
            raise _NotSatisfiable
        return max(0, size - length), size
    start = _bound(first)
    end = _bound(last) + 1 if last else size
    if last and end <= start:
        return None  # last before first: invalid, so ignored
    if start >= size:
        raise _NotSatisfiable
    return start, min(end, size)


async def _chain(first: bytes, rest: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    """The first piece, already pulled, then the rest.

    The stream closes however this ends.
    """
    try:
        if first:
            yield first
        async for piece in rest:
            yield piece
    finally:
        aclose = getattr(rest, "aclose", None)
        if aclose is not None:
            await aclose()


class _Body:
    """The request body as the backend pulls it, capped at ``limit`` bytes."""

    def __init__(self, stream: AsyncIterable[bytes], limit: int | None) -> None:
        self._stream = stream
        self._limit = limit
        self.started = False
        """Whether the backend has asked for a piece, so the body may be partly read."""

    async def pieces(self) -> AsyncIterator[bytes]:
        """The body piece by piece.

        Raises ``_UploadTooLarge`` past the limit, before that piece reaches
        the backend.
        """
        self.started = True
        size = 0
        async for piece in self._stream:
            if not piece:
                continue
            size += len(piece)
            if self._limit is not None and size > self._limit:
                raise _UploadTooLarge
            yield piece
