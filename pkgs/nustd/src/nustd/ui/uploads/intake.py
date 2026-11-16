"""The upload intake: the route that fills the temp area.

A file the person picks in the browser stays there until the program asks
for bytes. Then the browser POSTs them here, on a second connection beside
the ws, and the program hears a token back over the ws. Bytes never ride the
ws and the browser never learns a server path.

The route ``POST /_nu/upload/{sid}``: same origin only, live tabs only,
capped before and while streaming, written to ``.part`` and renamed when
whole. It answers ``{token, size}`` and nothing else.

Starlette lives only here. ``uploads`` imports this module when it builds the
route, so importing ``nustd.ui.uploads`` never loads a web server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .area import UPLOAD_PREFIX


if TYPE_CHECKING:
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
    """``POST /_nu/upload/{sid}``: one raw body into the area, answered with its token."""

    async def intake(request: Request) -> Response:
        if not same_origin(request):
            return _plain("cross-site upload refused", 403)
        sid = request.path_params["sid"]
        if not area.is_live(sid):
            return _plain("no live tab for this upload", 403)
        if _declared(request) > area.cap:
            return _too_large(area.cap)
        token, part = area.new(sid)
        size = 0
        try:
            with part.open("xb") as out:
                async for piece in request.stream():
                    size += len(piece)
                    if size > area.cap:
                        raise _TooLarge
                    out.write(piece)
            area.land(sid, token)
        except _TooLarge:
            part.unlink(missing_ok=True)
            return _too_large(area.cap)
        except ClientDisconnect:
            part.unlink(missing_ok=True)
            return Response(status_code=400)  # the client is gone; nobody reads this
        except OSError:
            part.unlink(missing_ok=True)
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
        return JSONResponse({"token": token, "size": size}, status_code=201)

    return Route(f"{UPLOAD_PREFIX}/{{sid}}", intake, methods=["POST"], name="nu_upload")


def _declared(request: Request) -> int:
    """The body size ``Content-Length`` claims, 0 when it is absent or not a number."""
    value = request.headers.get("content-length", "").strip()
    if not (value.isascii() and value.isdigit()):
        return 0
    value = value.lstrip("0") or "0"
    return int(value) if len(value) <= 19 else 1 << 64


def _plain(text: str, status: int) -> Response:
    return Response(text, status_code=status, media_type="text/plain")


def _too_large(cap: int) -> Response:
    return _plain(f"upload over the cap of {cap} bytes", 413)
