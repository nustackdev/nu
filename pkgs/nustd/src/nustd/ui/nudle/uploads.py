"""The upload intake: a temp area on disk and the route that fills it.

A file the person picks in the browser stays there until the program asks
for bytes. Then the browser POSTs them here, on a second connection beside
the ws, and the program hears a token back over the ws. Bytes never ride the
ws and the browser never learns a server path.

Two halves, built together by ``uploads`` so they share one area:

- ``UploadArea``, a fabric opened by a ``Provide`` bracket. It only manages
  the folder: one dir per tab under its root, one file per pull or slice,
  each tab's dir swept when its connection closes, the whole root removed
  when the server stops. It never opens a socket and never reads a file.
- the route ``POST /_nu/upload/{sid}``: same origin only, live tabs only,
  capped before and while streaming, written to ``.part`` and renamed when
  whole. It answers ``{token, size}`` and nothing else.

The program side reads one tab's corner of the area through
``nustd.ui.core.UploadView``, which ``upload_view`` binds in each arm.
"""

from __future__ import annotations

import shutil
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from nu.context.fabric import Provide
from nu.core.spans.bracket import _LifecycleBracket
from nustd.ui.core.uploads import UPLOAD_PREFIX, UploadView, check_token, tab_dir, upload_file
from nustd.ws_server.fabric import WebServer
from nustd.ws_server.interactions import SID_ATTR


if TYPE_CHECKING:
    import os
    from collections.abc import AsyncIterator

    from starlette.requests import Request

    from nu.lang import Nu
    from nu.lang.runtime import Context
    from nustd.ws_server.fabric import _Subscription


__all__ = ["DEFAULT_CAP", "STALE_AFTER", "UploadArea", "UploadViewFor", "upload_view", "uploads"]


#: The most bytes one POST may carry unless the host says otherwise.
DEFAULT_CAP = 2 << 30

#: A ``nu-uploads-*`` dir untouched this long belongs to a server that is gone.
STALE_AFTER = 24 * 60 * 60

_PREFIX = "nu-uploads-"
_PART = ".part"


class UploadArea:
    """The temp area of one ui server: a folder of files the tabs posted.

    Opened by the bracket ``uploads`` returns, inside the ws server's own
    bracket, and bound on the Context under ``UploadArea``. Setup makes the
    root, clears stale areas a dead server left behind, and hooks the
    server's connection book so a tab's dir goes when its socket closes.
    Cleanup removes the root.

    Args:
        root: the folder to keep files in. Made at setup if missing, removed
            whole at cleanup, so give it a dir of its own.
        cap: the most bytes one POST may carry.

    Notes:
        - Layout is ``root / sid / token``. A token is ``uuid4().hex``; a
          file still being written is ``token.part`` beside it.
        - Stale means untouched for a day: at setup any ``nu-uploads-*`` dir
          in the system temp dir, and anything inside ``root``, older than
          that is removed. A server idle for more than a day keeps working,
          it only loses what landed before.
        - ``path`` and ``drop`` are the same as on the ``UploadView`` a tab's
          program reads, so the host and a worker agree on every name.

    Example:
        bracket, routes = nustd.ui.nudle.uploads(root=".uploads")
        nu.With(listen(..., routes=routes), bracket, body=...)
    """

    def __init__(self, root: str | os.PathLike[str], cap: int = DEFAULT_CAP) -> None:
        if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
            msg = f"cap is a byte count, got {cap!r}"
            raise ValueError(msg)
        self._root = Path(root).absolute()
        self._cap = cap
        self._server: WebServer | None = None
        self._sub: _Subscription | None = None

    @property
    def root(self) -> Path:
        """The folder the area keeps its files in."""
        return self._root

    @property
    def cap(self) -> int:
        """The most bytes one POST may carry."""
        return self._cap

    # ---- lifecycle ----------------------------------------------------------

    def setup(self, ctx: Context) -> None:
        """Make the root, clear what is stale, and follow the server's tabs.

        Raises:
            LookupError: no ws server is open around this bracket. The area
                lives inside one: put it after ``listen(...)`` in the
                ``nu.With``.
        """
        if not ctx.fabrics.has(WebServer):
            msg = "UploadArea opens inside a ws server; put it after listen(...) in the nu.With"
            raise LookupError(msg)
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._sweep_stale(time.time() - STALE_AFTER)
        server = ctx.fabrics.get(WebServer)
        sub = server.subscribe()
        sub.bind(self._on_book)
        self._server = server
        self._sub = sub

    def cleanup(self) -> None:
        """Stop following the server and remove the root with all it holds."""
        if self._sub is not None:
            self._sub.close()
        self._sub = None
        self._server = None
        shutil.rmtree(self._root, ignore_errors=True)

    def _on_book(self, sid: object) -> None:
        """A connection opened or closed. A closed one loses its files."""
        if isinstance(sid, str) and not self.is_live(sid):
            self.sweep(sid)

    def _sweep_stale(self, before: float) -> None:
        here = self._root.resolve()
        for old in Path(tempfile.gettempdir()).glob(f"{_PREFIX}*"):
            if old.resolve() != here and old.is_dir() and _touched(old) < before:
                shutil.rmtree(old, ignore_errors=True)
        for old in self._root.iterdir():
            if _touched(old) < before:
                _remove(old)

    # ---- the folder ---------------------------------------------------------

    def is_live(self, sid: str) -> bool:
        """Whether ``sid`` is a connection the server holds open right now."""
        server = self._server
        return server is not None and server.session(sid) is not None

    def new(self, sid: str) -> tuple[str, Path]:
        """A fresh token for ``sid`` and the ``.part`` path to write it to."""
        home = tab_dir(self._root, sid)
        home.mkdir(mode=0o700, parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        return token, home / f"{token}{_PART}"

    def land(self, sid: str, token: str) -> Path:
        """Rename ``token.part`` to ``token``: the file is whole."""
        home = tab_dir(self._root, sid)
        final = home / check_token(token)
        (home / f"{token}{_PART}").rename(final)
        return final

    def path(self, sid: str, token: str) -> Path:
        """The landed file ``token`` names in ``sid``'s dir.

        Raises:
            ValueError: a malformed sid or token, or one resolving outside
                ``root / sid``.
            FileNotFoundError: nothing landed under it.
        """
        return upload_file(self._root, sid, token)

    def drop(self, sid: str, token: str) -> None:
        """Remove one file, and its ``.part`` if it is still being written."""
        home = tab_dir(self._root, sid)
        check_token(token)
        (home / token).unlink(missing_ok=True)
        (home / f"{token}{_PART}").unlink(missing_ok=True)

    def sweep(self, sid: str) -> None:
        """Remove everything ``sid`` posted."""
        shutil.rmtree(tab_dir(self._root, sid), ignore_errors=True)

    def view(self, sid: str) -> UploadView:
        """The resolve only view of this area for one tab."""
        return UploadView(self._root, sid)

    def __repr__(self) -> str:
        return f"UploadArea(root={str(self._root)!r}, cap={self._cap})"


def _touched(path: Path) -> float:
    """The latest mtime of ``path`` and, for a dir, what sits right in it."""
    try:
        latest = path.stat().st_mtime
        if path.is_dir():
            for child in path.iterdir():
                latest = max(latest, child.stat().st_mtime)
    except OSError:
        return float("inf")  # gone or unreadable meanwhile: not ours to judge
    return latest


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


# ---- the route --------------------------------------------------------------


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


# ---- the pair ---------------------------------------------------------------


def _held(area: UploadArea) -> UploadArea:
    """``Provide`` builds its fabric from a class; this hands back the one built already."""
    return area


def uploads(
    root: str | os.PathLike[str] | None = None,
    *,
    cap: int = DEFAULT_CAP,
) -> tuple[Provide, list[Route]]:
    """The temp area's bracket and its intake route, sharing one area.

    The root is fixed here, when the tree is built, not when the bracket
    opens: a host that hands workers the same root (nuspace) decides it
    before any server is up.

    Args:
        root: the folder for posted files, made at setup if missing and
            removed at cleanup. None picks a fresh ``nu-uploads-<hex>`` in
            the system temp dir, made at setup.
        cap: the most bytes one POST may carry. A bigger body is answered
            413, before reading when ``Content-Length`` says so, at the
            first byte past the cap otherwise.

    Returns:
        ``(bracket, routes)``. The bracket goes in the ``nu.With`` after the
        ws server's (it follows that server's connections); the routes go in
        that server's ``routes=``.

    Example:
        bracket, routes = uploads()
        nu.With(
            listen(session_cls=WsSession, routes=routes),
            bracket,
            body=sessions_fold(session_for(SID_ATTR, upload_view(SID_ATTR, program))),
        )
    """
    if root is None:
        root = Path(tempfile.gettempdir()) / f"{_PREFIX}{uuid.uuid4().hex}"
    area = UploadArea(root, cap)
    return Provide(_held, {"area": area}, bind_as=UploadArea), [_route(area)]


# ---- the program side -------------------------------------------------------


class UploadViewFor(_LifecycleBracket):
    """Bind this arm's ``UploadView``: the area, seen from one tab.

    Reads the sid the fold parked on the Context and binds the area's view
    for it, so the upload refs under it reach their tab's files and url
    without knowing the area or the host.

    Args:
        body: the tree that runs with the view bound.
        sid_attr: the attr the fold parked this arm's session id under.
    """

    def __init__(self, body: Nu | None = None, *, sid_attr: str = SID_ATTR) -> None:
        super().__init__(body)
        self._payload["sid_attr"] = sid_attr

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[None]:
        attr = self._payload["sid_attr"]
        sid = ctx.attrs.get(attr, None)
        if sid is None:
            msg = f"UploadViewFor found no {attr!r} on the Context; it runs inside the fold"
            raise LookupError(msg)
        if not ctx.fabrics.has(UploadArea):
            msg = "UploadViewFor found no UploadArea; open the uploads bracket around the fold"
            raise LookupError(msg)
        with ctx.fabrics.bind(UploadView, ctx.fabrics.get(UploadArea).view(sid)):
            yield


def upload_view(sid_attr: str = SID_ATTR, body: Nu | None = None) -> UploadViewFor:
    """``UploadViewFor`` in call order: the attr first, then what runs under it.

    Example:
        session_for(SID_ATTR, upload_view(SID_ATTR, run_once(program)))
    """
    return UploadViewFor(body, sid_attr=sid_attr)
