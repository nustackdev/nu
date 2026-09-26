"""``ValkeyRef``: the fabric ref that resolves the ``ValkeyServer`` bound on ctx.

A plain ``FabricRef``: the address is the fabric type, so the read is the
untagged binding, same as ``nustd.mp_pool.PoolRef``. It also carries this
fabric's fluent surface: ``ValkeyRef().url()`` and ``Url(ValkeyRef())`` build
the same term.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef

from .resources import ValkeyServer


if TYPE_CHECKING:
    from .interactions import Ping, Url


__all__ = ["ValkeyRef"]


class ValkeyRef(FabricRef):
    """The ``ValkeyServer`` bound on the Context.

    Notes:
        - Reading it is a lookup and nothing else; the server is not
          contacted.
        - The methods are a convenience over the constructors, each returning
          the same term the matching ``Url(...)`` / ``Ping(...)`` call would.

    Yields:
        The bound ``ValkeyServer``. EMPTY when nothing is bound.

    Example:
        With(nustd.valkey.server(".vk"), body=SetCmd(AttrRef("up"), ValkeyRef().ping()))
    """

    fabric = ValkeyServer

    # The interactions import this module, so the imports below are lazy.

    def url(self) -> Url:
        """A ``Url`` read on this server: the ``unix://`` URL clients connect with."""
        from .interactions import Url

        return Url(self)

    def ping(self) -> Ping:
        """A ``Ping`` read on this server: does it answer right now."""
        from .interactions import Ping

        return Ping(self)
