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
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

from nu.lang import Bracket

from ...session import session_id
from .area import _PREFIX, UploadArea, UploadView


if TYPE_CHECKING:
    import os
    from collections.abc import AsyncIterator, Iterator

    from starlette.routing import Route

    from nu.lang import Literal, Nu
    from nu.lang.runtime import Context


__all__ = ["UploadViewFor", "upload_view", "uploads"]


class _OpenArea(Bracket):
    """Open an area built already: set it up, bind it under ``UploadArea``, clean it up.

    ``uploads`` builds the area at tree build time, since its route needs the
    same instance before any server is up. This bracket is what opens that
    one instance for the body, through the area's own fabric lifecycle:
    ``setup`` / ``cleanup`` under ``nu.run``, ``asetup`` / ``acleanup`` under
    ``nu.arun``. Cleanup only runs when setup completed.

    Args:
        area: the area to open. A config child, carried as given.
        body: the tree that runs with the area bound.
    """

    def __init__(self, area: UploadArea, body: Nu | None = None) -> None:
        super().__init__(body, area)

    @property
    def area(self) -> UploadArea:
        """The area this bracket opens, the same instance its route writes to."""
        return cast("UploadArea", cast("Literal", self._children[1]).value)

    @contextmanager
    def _open(self, ctx: Context, area: UploadArea) -> Iterator[Context]:
        area.setup(ctx)
        try:
            yield ctx.bind(UploadArea, area)
        finally:
            area.cleanup()

    @asynccontextmanager
    async def _aopen(self, ctx: Context, area: UploadArea) -> AsyncIterator[Context]:
        await area.asetup(ctx)
        try:
            yield ctx.bind(UploadArea, area)
        finally:
            await area.acleanup()


def uploads(
    root: str | os.PathLike[str] | None = None,
    *,
    cap: int | None = None,
) -> tuple[_OpenArea, list[Route]]:
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
        that server's ``routes=``. ``bracket.area`` is the area both share.

    Example:
        bracket, routes = uploads()
        nu.With(
            listen(session_cls=WsSession, routes=routes),
            bracket,
            body=sessions_fold(lambda sid: session_for(sid, upload_view(program))),
        )
    """
    if root is None:
        root = Path(tempfile.gettempdir()) / f"{_PREFIX}{uuid.uuid4().hex}"
    # Here, not at the top: the route is starlette's, and importing this
    # package must not load it.
    from .intake import _route

    area = UploadArea(root, cap)
    return _OpenArea(area), [_route(area)]


# ---- the program side -------------------------------------------------------


class UploadViewFor(Bracket):
    """Bind this arm's ``UploadView``: the area, seen from one tab.

    Reads the session id ``session_for`` bound for the arm
    (``nustd.session.SessionId``) and binds the area's view for it, so the
    upload refs under it reach their tab's files and url without knowing
    the area or the host.

    Args:
        body: the tree that runs with the view bound.
    """

    def __init__(self, body: Nu | None = None) -> None:
        super().__init__(body)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        sid = session_id(ctx, "UploadViewFor")
        if not ctx.has(UploadArea):
            msg = "UploadViewFor found no UploadArea; open the uploads bracket around the fold"
            raise LookupError(msg)
        yield ctx.bind(UploadView, ctx.get(UploadArea).view(sid))


def upload_view(body: Nu | None = None) -> UploadViewFor:
    """``UploadViewFor`` over ``body``, inside ``session_for``.

    Example:
        sessions_fold(lambda sid: session_for(sid, upload_view(run_once(program))))
    """
    return UploadViewFor(body)
