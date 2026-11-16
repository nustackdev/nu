"""``UploadView`` -- one tab's corner of the upload area, as the refs see it.

The bytes of a picked file reach the server over http, into a temp area the
host owns (``nustd.ui.nudle.uploads``). A program reading a landed file needs
three things from that area and nothing else: its tab's sid, the intake url
the browser posts to, and the file a token names. This view is exactly that,
bound on the Context for one tab.

It lives in core, not beside the area, because the refs read it and a worker
drawing over a pipe never loads the server. The host binds it in each arm;
a worker host binds one it builds itself from the same root, so the refs
cannot tell where they run.

Layout, shared with the area: ``root / sid / token``, one dir per tab, one
file per pull or slice. A token is ``uuid4().hex``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import os


__all__ = ["UPLOAD_PREFIX", "UploadView", "check_sid", "check_token", "tab_dir", "upload_file"]


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
    The host binds one per tab (``nustd.ui.nudle.upload_view`` in nudle's
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
