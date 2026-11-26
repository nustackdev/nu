"""The session id: which connection an arm of the ws fold belongs to.

``SessionId`` is the Shape the id lives under. ``nustd.ws_server.session_for``
binds it statically for its body, a frame of its own per arm, so arms never
see each other's id. Trees read it through the ref, ``SessionId.sid``;
Python bracket code reads it off the Context like any mem frame, with
:func:`session_id`.

Its own module, holding nothing but the Shape, so a reader such as
``nustd.ui.uploads`` imports it without loading the web server that
``nustd.ws_server`` brings in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["SessionId", "session_id"]


class SessionId(nu.Shape):
    """The id of the connection this arm serves, bound by ``session_for``."""

    sid = nu.StrRef.slot()


def session_id(ctx: Context, owner: str) -> str:
    """The session id bound on ``ctx``, for Python bracket code.

    Raises:
        LookupError: no ``session_for`` frame is in scope; the message names
            ``owner``.
    """
    sid = ctx.get(dict, SessionId).get("sid") if ctx.has(dict, SessionId) else None
    if sid is None:
        msg = f"{owner} found no session id on the Context; it runs inside session_for"
        raise LookupError(msg)
    return str(sid)
