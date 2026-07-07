"""``InvisiblesProxy``: bracket that provisions an ``InvisiblesClient`` and
binds its ``.root`` proxy under a caller-named fabric type.

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

from nu.spans.bracket import _LifecycleBracket

from .client import InvisiblesClient


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["InvisiblesProxy"]


class InvisiblesProxy(_LifecycleBracket):
    """Provide an ``InvisiblesClient`` and bind its ``.root`` as ``target``."""

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

    def __repr__(self) -> str:
        target = self._payload.get("target")
        addr = self._payload.get("client_kwargs", {}).get("address")
        return f"InvisiblesProxy({target.__name__ if target else '?'}, address={addr!r})"
