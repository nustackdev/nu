"""The upload area: a temp folder of picked files, and one tab's view of it.

The bytes of a picked file reach the server over http, into a temp area the
host owns. A program reading a landed file needs three things from that area
and nothing else: its tab's sid, the intake url the browser posts to, and the
file a token names. ``UploadView`` is exactly that, bound on the Context for
one tab.

- ``UploadArea``, a fabric opened by a ``Provide`` bracket. It only manages
  the folder: one dir per tab under its root, one file per pull or slice,
  each tab's dir swept when its connection closes, the whole root removed
  when the server stops. It never opens a socket and never reads a file.
- ``UploadView``, the resolve only view the refs read. A worker drawing over
  a pipe builds one from the same root, so the refs cannot tell where they
  run.

Nothing here loads the web server: the refs import this module, and a worker
never serves. ``UploadArea`` reaches the ws server only when it opens.

Layout, shared by both: ``root / sid / token``, one dir per tab, one file per
pull or slice. A token is ``uuid4().hex``.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from nu.context.fabric import Fabric


if TYPE_CHECKING:
    import os

    from nu.lang.runtime import Context
    from nustd.ws_server.fabric import WebServer, _Subscription


__all__ = [
    "STALE_AFTER",
    "UPLOAD_PREFIX",
    "UploadArea",
    "UploadView",
    "check_sid",
    "check_token",
    "tab_dir",
    "upload_file",
]


#: Where the intake route sits. A tab posts to ``{UPLOAD_PREFIX}/{sid}``.
UPLOAD_PREFIX = "/_nu/upload"

_TOKEN = re.compile(r"[0-9a-f]{32}", re.ASCII)

# One plain path segment: a uuid hex from the server, or whatever id a host
# hands its tabs, as long as it cannot climb out of the root.
_SID = re.compile(r"[0-9A-Za-z_-]{1,128}", re.ASCII)


def check_token(token: object) -> str:
    """``token`` when it is 32 lowercase hex chars, else ``ValueError``."""
    if not isinstance(token, str) or _TOKEN.fullmatch(token) is None:
        msg = f"not an upload token: {token!r}"
        raise ValueError(msg)
    return token


def check_sid(sid: object) -> str:
    """``sid`` when it is one safe path segment, else ``ValueError``."""
    if not isinstance(sid, str) or _SID.fullmatch(sid) is None:
        msg = f"not a session id: {sid!r}"
        raise ValueError(msg)
    return sid


def tab_dir(root: Path, sid: str) -> Path:
    """The dir holding one tab's files: ``root / sid``."""
    return root / check_sid(sid)


def upload_file(root: Path, sid: str, token: str) -> Path:
    """The landed file ``token`` names in ``sid``'s dir.

    Raises:
        ValueError: the sid or the token is malformed, or the path resolves
            outside ``root / sid`` (a symlink planted in the dir).
        FileNotFoundError: nothing landed under that token, or it was dropped.
    """
    home = tab_dir(root, sid)
    file = home / check_token(token)
    real = file.resolve()
    if real.parent != home.resolve():
        msg = f"upload {token!r} resolves outside its tab's dir"
        raise ValueError(msg)
    if not real.is_file():
        msg = f"no upload {token!r} for this tab"
        raise FileNotFoundError(msg)
    return real


class UploadView:
    """One tab's resolve only view of the upload area.

    No route, no sweep, no lifecycle: it names files, it never makes them.
    The host binds one per tab (``nustd.ui.uploads.upload_view`` in nudle's
    arm, its own bracket in a worker) and the upload refs read it with
    ``ctx.fabrics.get(UploadView)``.

    Args:
        root: the area's root dir, the same one the host's area writes into.
        sid: the tab this view serves.

    Notes:
        - The browser never sees a path: it gets ``url`` to post to and is
          answered with a token. The path is resolved here, on the program
          side.
        - Two views over one root and sid are interchangeable, so a worker
          building its own sees what the host's area landed.

    Example:
        view = UploadView("/tmp/nu-uploads-ab12", sid)
        view.url                      # "/_nu/upload/<sid>"
        view.path(token).read_bytes()
        view.drop(token)
    """

    __slots__ = ("_root", "_sid")

    def __init__(self, root: str | os.PathLike[str], sid: str) -> None:
        self._root = Path(root)
        self._sid = check_sid(sid)

    @property
    def root(self) -> Path:
        """The area's root dir."""
        return self._root

    @property
    def sid(self) -> str:
        """The tab this view serves."""
        return self._sid

    @property
    def url(self) -> str:
        """The intake url this tab posts bytes to, same origin, no host."""
        return f"{UPLOAD_PREFIX}/{self._sid}"

    def path(self, token: str) -> Path:
        """The landed file ``token`` names. See ``upload_file`` for what it refuses."""
        return upload_file(self._root, self._sid, token)

    def drop(self, token: str) -> None:
        """Remove the file ``token`` names. Gone already is fine."""
        (tab_dir(self._root, self._sid) / check_token(token)).unlink(missing_ok=True)

    def __repr__(self) -> str:
        return f"UploadView(root={str(self._root)!r}, sid={self._sid!r})"


# ---- the area -------------------------------------------------------------


#: A ``nu-uploads-*`` dir untouched this long belongs to a server that is gone.
STALE_AFTER = 24 * 60 * 60

_PREFIX = "nu-uploads-"
_PART = ".part"


class UploadArea(Fabric):
    """The temp area of one ui server: a folder of files the tabs posted.

    Opened by the bracket ``uploads`` returns, inside the ws server's own
    bracket, and bound on the Context under ``UploadArea``. Setup makes the
    root, clears stale areas a dead server left behind, and hooks the
    server's connection book so a tab's dir goes when its socket closes.
    Cleanup removes the root.

    Args:
        root: the folder to keep files in. Made at setup if missing, removed
            whole at cleanup, so give it a dir of its own.
        cap: the most bytes one file may carry, whole or in pieces. None,
            the default, takes any size: the disk is the limit, and a write
            that finds it full is answered as such.

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
        bracket, routes = nustd.ui.uploads.uploads(root=".uploads")
        nu.With(listen(..., routes=routes), bracket, body=...)
    """

    def __init__(self, root: str | os.PathLike[str], cap: int | None = None) -> None:
        if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 0):
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
    def cap(self) -> int | None:
        """The most bytes one file may carry; None for any size."""
        return self._cap

    # ---- lifecycle ----------------------------------------------------------

    def setup(self, ctx: Context) -> None:
        """Make the root, clear what is stale, and follow the server's tabs.

        Raises:
            LookupError: no ws server is open around this bracket. The area
                lives inside one: put it after ``listen(...)`` in the
                ``nu.With``.
        """
        # Here, not at the top: the ws server loads uvicorn and starlette, and
        # importing the area must not.
        from nustd.ws_server.fabric import WebServer

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
