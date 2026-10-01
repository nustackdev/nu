"""The interactions of the ``nustd.valkey`` fabric.

Two reads over one ``ValkeyServer``: ``Url`` and ``Ping``. Starting and
stopping are not interactions. The server's whole lifecycle is its ``Provide``
bracket, the same way ``nustd.mp``'s one process is, because everything that
talks to it (a kv stack's publisher and observer) is bound inside that bracket
and a server stopped mid-body would pull the floor out from under them.

The server address is a **child**, never payload, so it can come from any Ref
or query.

==========  =========  ===========
atom        slots      sort
==========  =========  ===========
Url         (server,)  ScalarQuery
Ping        (server,)  ScalarQuery
==========  =========  ===========
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Nu, ScalarQuery
from nu.lang.sentinels import EMPTY

from .refs import ValkeyRef
from .resources import ValkeyServer


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Ping", "Url"]


def _server_node(server: Nu | None) -> Nu:
    """The server slot: whatever was passed, or the untagged ``ValkeyRef``."""
    return ValkeyRef() if server is None else server


def _require_server(value: object) -> ValkeyServer:
    """Unwrap the server slot's value, refusing sentinels with a usable message."""
    if value is EMPTY or value is None:
        msg = "no ValkeyServer is bound on the Context; wrap the tree in nustd.valkey.server(...)"
        raise RuntimeError(msg)
    if not isinstance(value, ValkeyServer):
        msg = f"the server slot yielded {type(value).__name__}, not a ValkeyServer"
        raise TypeError(msg)
    return value


class Url(ScalarQuery):
    """The ``unix://`` URL a Redis client reaches the bound server with.

    Args:
        server: the node yielding the ``ValkeyServer``. Defaults to the
            untagged ``ValkeyRef``.

    Notes:
        - The same string ``nustd.valkey.url_for(data_dir)`` builds without a
          server, which is what a kv preset built outside the tree needs. This
          read is for the tree that wants it from the bound server itself.
        - A pure read; the server is not contacted.

    Yields:
        The URL, a str.

    Example:
        With(nustd.valkey.server(".vk"), body=Print(STDOUT, Url()))
    """

    def __init__(self, server: Nu | None = None) -> None:
        super().__init__(_server_node(server))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync url thunk."""

        def thunk(rt: Runtime) -> object:
            return _require_server(children[0](rt)).url

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async url thunk."""

        async def athunk(rt: Runtime) -> object:
            return _require_server(await children[0](rt)).url

        return athunk


class Ping(ScalarQuery):
    """Whether the bound server answers a ``PING`` right now.

    Args:
        server: the node yielding the ``ValkeyServer``. Defaults to the
            untagged ``ValkeyRef``.

    Notes:
        - A real round trip over the unix socket, not a process check, so a
          wedged server reads False.
        - Never raises for a dead server; that is what False is for.

    Yields:
        True or False.

    Example:
        With(nustd.valkey.server(".vk"), body=Ping())
    """

    def __init__(self, server: Nu | None = None) -> None:
        super().__init__(_server_node(server))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync ping thunk."""

        def thunk(rt: Runtime) -> object:
            return _require_server(children[0](rt)).ping()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async ping thunk."""

        async def athunk(rt: Runtime) -> object:
            return await _require_server(await children[0](rt)).aping()

        return athunk
