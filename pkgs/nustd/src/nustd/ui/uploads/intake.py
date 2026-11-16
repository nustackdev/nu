"""The upload intake: the route that fills the temp area.

A file the person picks in the browser stays there until the program asks
for bytes. Then the browser POSTs them here, on a second connection beside
the ws, and the program hears a token back over the ws. Bytes never ride the
ws and the browser never learns a server path.

The route ``POST /_nu/upload/{sid}``: same origin only, live tabs only,
capped before and while streaming when the area has a cap, written to
``.part`` and renamed when whole. It answers ``{token, size}`` and nothing
else. A disk that fills mid write drops the ``.part`` and is answered
``507``, so the tab says so instead of a broken transfer.

A large file goes up in pieces, so a dropped connection costs one piece and
not the file. The query says which piece:

- none: the body is the whole file, landed at once (``201``).
- ``?total=N``: the first piece of an ``N`` byte file. It mints the token;
  ``202`` while the file is not whole yet, ``201`` once it is.
- ``?token=T&offset=K&total=N``: the piece at byte ``K``. The ``.part`` is
  cut back to ``K`` first, so a piece sent twice lands once. Past what
  arrived is ``409``, answered with the size the server has; a piece of a
  file already whole is answered ``201`` again.

Starlette lives only here. ``uploads`` imports this module when it builds the
route, so importing ``nustd.ui.uploads`` never loads a web server.
"""

from __future__ import annotations

import asyncio
import errno
import weakref
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .area import UPLOAD_PREFIX, check_token, tab_dir


if TYPE_CHECKING:
    from pathlib import Path

    from starlette.requests import Request

    from .area import UploadArea


__all__ = ["same_origin"]


class _TooLarge(Exception):  # noqa: N818 - a state, not an error kind
    """The body passed the cap while streaming."""


def same_origin(request: Request) -> bool:
    """Whether the request came from a page served by this same origin.

    A browser sends ``Sec-Fetch-Site`` on every request and a page cannot
    forge it, so when it is there it decides alone: only ``same-origin``
    passes. Without it, ``Origin`` must name the host the request reached.
    A request with neither is refused: any page on any site can POST to
    localhost, and a client that hides where it came from is one of them.
    """
    site = request.headers.get("sec-fetch-site")
    if site is not None:
        return site.strip().lower() == "same-origin"
    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if not origin or not host:
        return False
    parts = urlsplit(origin.strip())
    return parts.scheme in ("http", "https") and parts.netloc.lower() == host.strip().lower()


def _route(area: UploadArea) -> Route:
    """``POST /_nu/upload/{sid}``: a whole body or one piece of it, answered with its token."""
    # One piece of a file at a time: a retry can reach the server while the
    # piece it repeats is still streaming in.
    locks: weakref.WeakValueDictionary[str, asyncio.Lock] = weakref.WeakValueDictionary()

    async def intake(request: Request) -> Response:
        if not same_origin(request):
            return _plain("cross-site upload refused", 403)
        sid = request.path_params["sid"]
        if not area.is_live(sid):
            return _plain("no live tab for this upload", 403)
        query = request.query_params
        if "total" not in query:
            if _over(area, _declared(request)):
                return _too_large(area.cap)
            token, part = area.new(sid)
            return await _fill(request, area, sid, token, part, 0, None, keep=False)
        total = _count(query.get("total"))
        if total is None:
            return _plain("total is a byte count", 400)
        if _over(area, total):
            return _too_large(area.cap)
        if "token" not in query:
            token, part = area.new(sid)
            return await _fill(request, area, sid, token, part, 0, total, keep=False)
        try:
            token = check_token(query.get("token"))
        except ValueError:
            return _plain("not an upload token", 400)
        offset = _count(query.get("offset"))
        if offset is None or offset > total:
            return _plain("offset is a byte count within total", 400)
        lock = locks.get(token)
        if lock is None:
            lock = locks[token] = asyncio.Lock()
        async with lock:
            return await _piece(request, area, sid, token, offset, total)

    return Route(f"{UPLOAD_PREFIX}/{{sid}}", intake, methods=["POST"], name="nu_upload")


async def _piece(
    request: Request, area: UploadArea, sid: str, token: str, offset: int, total: int
) -> Response:
    """The piece at ``offset`` of the file ``token``, after the first."""
    home = tab_dir(area.root, sid)
    whole, part = home / token, home / f"{token}.part"
    if whole.is_file() and whole.stat().st_size == total:
        return JSONResponse({"token": token, "size": total}, status_code=201)
    if not part.is_file():
        return _plain("no upload under this token", 404)
    have = part.stat().st_size
    if offset > have:
        return JSONResponse({"token": token, "size": have}, status_code=409)
    return await _fill(request, area, sid, token, part, offset, total, keep=True)


async def _fill(
    request: Request,
    area: UploadArea,
    sid: str,
    token: str,
    part: Path,
    offset: int,
    total: int | None,
    *,
    keep: bool,
) -> Response:
    """Write the body into ``part`` at ``offset``; land it once the file is whole.

    ``total`` is the file's size, already under the cap: a body running past
    it is cut and the part dropped. None is a whole body, bound by the cap
    and landed when it ends. ``keep`` holds a part a dropped connection
    broke, so the next try of the piece goes on from it.
    """
    limit = area.cap if total is None else total
    size = offset
    try:
        with part.open("r+b" if keep else "xb") as out:
            out.seek(offset)
            out.truncate()
            async for piece in request.stream():
                size += len(piece)
                if limit is not None and size > limit:
                    raise _TooLarge
                out.write(piece)
        whole = total is None or size == total
        if whole:
            area.land(sid, token)
    except _TooLarge:
        part.unlink(missing_ok=True)
        return _too_large(area.cap) if total is None else _plain("past the declared total", 400)
    except ClientDisconnect:
        if not keep:
            part.unlink(missing_ok=True)
        return Response(status_code=400)  # the client is gone; nobody reads this
    except OSError as exc:
        part.unlink(missing_ok=True)
        if exc.errno in _FULL:
            return _plain("no space left on the server for this upload", 507)
        if area.is_live(sid):
            raise
        return _plain("no live tab for this upload", 403)  # its dir was swept under us
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    if not area.is_live(sid):
        # The tab closed while its bytes streamed in, after its sweep ran.
        area.drop(sid, token)
        return _plain("no live tab for this upload", 403)
    return JSONResponse({"token": token, "size": size}, status_code=201 if whole else 202)


def _count(value: str | None) -> int | None:
    """A non negative byte count from the query, None when it is not one."""
    if value is None or not (value.isascii() and value.isdigit()) or len(value) > 19:
        return None
    return int(value)


def _declared(request: Request) -> int:
    """The body size ``Content-Length`` claims, 0 when it is absent or not a number."""
    value = request.headers.get("content-length", "").strip()
    if not (value.isascii() and value.isdigit()):
        return 0
    value = value.lstrip("0") or "0"
    return int(value) if len(value) <= 19 else 1 << 64


def _plain(text: str, status: int) -> Response:
    return Response(text, status_code=status, media_type="text/plain")


#: What a write to a full disk, or past a quota, raises.
_FULL = frozenset({errno.ENOSPC, errno.EDQUOT, errno.EFBIG})


def _over(area: UploadArea, size: int) -> bool:
    """Whether ``size`` bytes are over the area's cap; never when it has none."""
    return area.cap is not None and size > area.cap


def _too_large(cap: int | None) -> Response:
    return _plain(f"upload over the cap of {cap} bytes", 413)
