"""``InvisiblesProxy``: bracket for a client-bound remote fabric.

Provisions an ``InvisiblesClient`` and binds its ``.root`` proxy under a
caller-named fabric type.

The common pattern is "connect to an invisibles-hosted Navigator and let the
rest of the tree talk to it as a plain ``Navigator``". Without this bracket a
caller would write two nested Provides and a re-bind fabric; ``InvisiblesProxy``
collapses that::

    InvisiblesProxy(Navigator, address="10.0.0.1:19000",
        body,
    )

is equivalent to constructing an ``InvisiblesClient``, running its ``asetup``,
and binding ``client.root`` on ctx under ``Navigator`` (with optional tag).
Teardown closes the connection when the body finishes.

Extra client kwargs (``transport``, ``timeout``, ``max_retries``,
``bg_serve``, ``buffered_iteration``) pass through.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.core.spans.bracket import _LifecycleBracket

from .client import InvisiblesClient


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["InvisiblesProxy"]


class InvisiblesProxy(_LifecycleBracket):
    """Runs its body against a remote fabric as if the fabric were local.

    Connects to an ``InvisiblesServer``, takes the root fabric it serves, and
    binds that remote object on the context under the type the caller names.
    Everything below reads the name and gets the proxy, so a tree written
    against a local fabric runs unchanged against a remote one, and the
    transport is a line at the top rather than a change to the body.

    Args:
        target: the fabric type the remote root is bound under. What the
            body asks the context for.
        body: what runs while the connection is open.

    Notes:
        - Async only. A sync run raises, because connecting is lifecycle work
          the sync path refuses to do.
        - Two things land on the context, both under ``tag``: the remote root
          under ``target``, and the ``InvisiblesClient`` itself, so a body can
          reach the connection when it needs to.
        - A ``target`` carrying ``_nu_bind_as`` binds under that type instead,
          the same redirection ``Provide`` honours.
        - Connecting retries up to ``max_retries`` times with a growing pause
          between attempts, and raises ConnectionError when they all fail.
        - Calls on the bound root block the caller for the round trip even
          under the async runtime: invisibles frames them synchronously.
        - ``bg_serve`` runs a background serving thread, needed when the
          remote side calls back into this process.
        - The connection closes when the body finishes, so nothing survives
          the bracket.

    Yields:
        The body's yield, unchanged. Transparent in cardinality too: a stream
        body stays a stream, and the connection stays open across the drain.

    Example:
        app = nu.proxy.InvisiblesProxy(
            Navigator,
            address="10.0.0.1:19000",
            body=driver_body,
        )
    """

    def __init__(
        self,
        target: type,
        body: Nu | None = None,
        *,
        address: str,
        tag: object = None,
        transport: str = "tcp",
        timeout: float = 5.0,
        max_retries: int = 3,
        bg_serve: bool = False,
        buffered_iteration: bool = True,
    ) -> None:
        super().__init__(body)
        self._payload["target"] = target
        self._payload["tag"] = tag
        self._payload["client_kwargs"] = {
            "address": address,
            "transport": transport,
            "timeout": timeout,
            "max_retries": max_retries,
            "bg_serve": bg_serve,
            "buffered_iteration": buffered_iteration,
        }

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        msg = "InvisiblesProxy requires the async runtime; use arun / afirst / acollect"
        raise RuntimeError(msg)
        yield ctx  # pragma: no cover -- generator-shape marker

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        target = self._payload["target"]
        tag = self._payload["tag"]
        tags = (tag,) if tag is not None else ()
        kwargs = self._payload["client_kwargs"]
        bind_as = getattr(target, "_nu_bind_as", None) or target

        client = InvisiblesClient(**kwargs)
        try:
            await client.asetup(ctx)
            scoped = ctx.bind(InvisiblesClient, client, *tags)
            scoped = scoped.bind(bind_as, client.root, *tags)
            yield scoped
        finally:
            await client.acleanup()
