"""The upload presets: the area and its route as one pair, and each tab's view.

Two halves, built together by ``uploads`` so they share one area: the
``UploadArea`` bracket and the intake route. A host mounts both; nudle's
``serve`` does, and nuspace will.

The program side reads one tab's corner of the area through ``UploadView``,
which ``upload_view`` binds in each arm.
"""

from __future__ import annotations

import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from nu.context.fabric import Fabric, Provide
from nu.lang import Bracket

from .area import _PREFIX, UploadArea, UploadView


if TYPE_CHECKING:
    import os
    from collections.abc import AsyncIterator

    from starlette.routing import Route

    from nu.lang import Nu, StrArg
    from nu.lang.runtime import Context


__all__ = ["UploadViewFor", "upload_view", "uploads"]


#: ``nustd.ws_server.SID_ATTR``, spelled here: that package loads the web
#: server on import, and importing this one must not.
_SID_ATTR = "sid"


class _Held(Fabric):
    """``Provide`` builds its fabric from a class; this one hands back the area built already.

    ``__new__`` returns the given area, so ``Provide`` sets up, binds and
    cleans up that area itself, not an instance of this class.
    """

    def __new__(cls, area: UploadArea) -> UploadArea:  # type: ignore[misc]
        return area


def uploads(
    root: str | os.PathLike[str] | None = None,
    *,
    cap: int | None = None,
) -> tuple[Provide, list[Route]]:
    """The temp area's bracket and its intake route, sharing one area.

    The root is fixed here, when the tree is built, not when the bracket
    opens: a host that hands workers the same root (nuspace) decides it
    before any server is up.

    Args:
        root: the folder for posted files, made at setup if missing and
            removed at cleanup. None picks a fresh ``nu-uploads-<hex>`` in
            the system temp dir, made at setup.
        cap: the most bytes one file may carry, whole or in pieces. A
            bigger file is answered 413, before reading when its size is
            declared, at the first byte past the cap otherwise. None, the
            default, takes any size; a disk that fills mid write is
            answered 507.

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
    # Here, not at the top: the route is starlette's, and importing this
    # package must not load it.
    from .intake import _route

    area = UploadArea(root, cap)
    return Provide(_Held, {"area": area}, bind_as=UploadArea), [_route(area)]


# ---- the program side -------------------------------------------------------


class UploadViewFor(Bracket):
    """Bind this arm's ``UploadView``: the area, seen from one tab.

    Reads the sid the fold parked on the Context and binds the area's view
    for it, so the upload refs under it reach their tab's files and url
    without knowing the area or the host.

    Args:
        body: the tree that runs with the view bound.
        sid_attr: the attr the fold parked this arm's session id under: a
            str, or any Nu yielding one. A config child, evaluated on entry.
    """

    def __init__(self, body: Nu | None = None, *, sid_attr: StrArg = _SID_ATTR) -> None:
        super().__init__(body, sid_attr)

    @asynccontextmanager
    async def _aopen(self, ctx: Context, sid_attr: str) -> AsyncIterator[None]:
        attr = sid_attr
        sid = ctx.attrs.get(attr, None)
        if sid is None:
            msg = f"UploadViewFor found no {attr!r} on the Context; it runs inside the fold"
            raise LookupError(msg)
        if not ctx.fabrics.has(UploadArea):
            msg = "UploadViewFor found no UploadArea; open the uploads bracket around the fold"
            raise LookupError(msg)
        with ctx.fabrics.bind(UploadView, ctx.fabrics.get(UploadArea).view(sid)):
            yield


def upload_view(sid_attr: str = _SID_ATTR, body: Nu | None = None) -> UploadViewFor:
    """``UploadViewFor`` in call order: the attr first, then what runs under it.

    Example:
        session_for(SID_ATTR, upload_view(SID_ATTR, run_once(program)))
    """
    return UploadViewFor(body, sid_attr=sid_attr)
